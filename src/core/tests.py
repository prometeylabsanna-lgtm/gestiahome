from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.models import SiteSettings


class LanguageTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        cache.clear()
        SiteSettings.objects.update_or_create(pk=1, defaults={"en_enabled": True})
        cache.clear()

    def test_double_prefix_collapses(self):
        response = self.client.get("/en/en/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/")

    def test_switch_roundtrip(self):
        response = self.client.post("/i18n/setlang/", {"language": "en", "next": "/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/")
        response = self.client.post("/i18n/setlang/", {"language": "uk", "next": "/en/katalog/"})
        self.assertEqual(response["Location"], "/katalog/")

    def test_currency_keeps_language(self):
        session = self.client.session
        session["currency"] = "uah"
        session.save()
        self.client.cookies.load({})
        self.client.post("/i18n/setlang/", {"language": "en", "next": "/katalog/"})
        response = self.client.post(
            "/i18n/setcurrency/",
            {"currency": "eur", "next": "/en/katalog/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/katalog/")
        self.assertEqual(self.client.session.get("currency"), "eur")

    def test_languages_are_uk_en_and_fr(self):
        self.assertEqual([code for code, _label in settings.LANGUAGES], ["uk", "en", "fr"])

    def test_ru_prefix_redirects_to_uk_path(self):
        response = self.client.get("/ru/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/")

    def test_ru_prefix_keeps_path_and_query(self):
        response = self.client.get("/ru/katalog/?q=shyshky")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/katalog/?q=shyshky")

    def test_repeated_ru_prefix_and_english_tail(self):
        response = self.client.get("/ru/ru/en/katalog/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/en/katalog/")

    def test_set_language_drops_retired_prefix(self):
        response = self.client.post("/i18n/setlang/", {"language": "ru", "next": "/ru/tovar/seo-box/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/tovar/seo-box/")

    def test_disabled_english_redirects_home(self):
        SiteSettings.objects.filter(pk=1).update(en_enabled=False)
        cache.clear()
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_disabled_french_redirects_home(self):
        SiteSettings.objects.filter(pk=1).update(fr_enabled=False)
        cache.clear()
        response = self.client.get("/fr/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")


class NotFoundTests(TestCase):
    @override_settings(DEBUG=False)
    def test_custom_404_page(self):
        response = self.client.get("/no-such-gestia-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Сторінку не знайдено", status_code=404)
        self.assertContains(response, "На головну", status_code=404)
        self.assertContains(response, "css/pages/utility.css", status_code=404)

    @override_settings(DEBUG=False)
    def test_missing_product_renders_404_page(self):
        response = self.client.get("/tovar/no-such-gestia-product/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Сторінку не знайдено", status_code=404)
        self.assertContains(response, "util-page--error", status_code=404)
        self.assertNotContains(response, "Page not found", status_code=404)


class ServerErrorTests(TestCase):
    @override_settings(DEBUG=False)
    def test_handler_renders_static_500_page(self):
        from config import urls as root_urls

        pattern = next(item for item in root_urls.urlpatterns if getattr(item, "name", None) == "healthz")
        client = Client(raise_request_exception=False)
        with patch.object(pattern, "callback", side_effect=RuntimeError("gestia-test-500")):
            response = client.get("/healthz/")
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Щось пішло не так", status_code=500)
        self.assertContains(response, "Something went wrong", status_code=500)
        self.assertContains(response, 'href="/"', status_code=500)
        self.assertContains(response, "#241c16", status_code=500)
        self.assertContains(response, "#f3eee6", status_code=500)
        self.assertContains(response, "#8d3b2a", status_code=500)
        self.assertNotContains(response, "gestia-test-500", status_code=500)
        self.assertNotContains(response, "htmx", status_code=500)


class SeoTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        cache.clear()
        SiteSettings.objects.update_or_create(pk=1, defaults={"en_enabled": True})
        cache.clear()
        self.category = Category.objects.create(slug="seo-cat", name_uk="Святкові бокси", is_active=True)
        self.product = Product.objects.create(
            category=self.category,
            sku="SEO-1",
            slug="seo-box",
            name_uk="Святковий бокс",
            seo_description_uk="Опис святкового боксу для столу.",
            price_uah=Decimal("100.00"),
            price_eur=Decimal("2.00"),
            is_active=True,
            stock_qty=100,
        )
        Product.objects.create(
            category=self.category,
            sku="SEO-OFF",
            slug="seo-hidden",
            name_uk="Прихований",
            price_uah=Decimal("10.00"),
            price_eur=Decimal("1.00"),
            is_active=False,
            stock_qty=100,
        )
        Category.objects.create(slug="seo-empty", name_uk="Порожня", is_active=True)
        parent = Category.objects.create(slug="seo-parent", name_uk="Батько", is_active=True)
        child = Category.objects.create(slug="seo-child", name_uk="Дитина", parent=parent, is_active=True)
        Product.objects.create(
            category=child,
            sku="SEO-CHILD",
            slug="seo-child-box",
            name_uk="Дитячий бокс",
            price_uah=Decimal("50.00"),
            price_eur=Decimal("1.00"),
            is_active=True,
            stock_qty=100,
        )

    def tearDown(self):
        translation.activate("uk")
        cache.clear()

    def test_home_and_product_have_canonical_and_og_title(self):
        home = self.client.get("/")
        self.assertContains(home, '<link rel="canonical" href="http://testserver/">')
        self.assertContains(home, '<meta property="og:title" content="Gestia Home">')
        self.assertContains(home, '<meta property="og:site_name" content="Gestia Home">')
        self.assertContains(home, '<title>Gestia Home</title>')
        self.assertContains(home, 'hreflang="uk"')
        self.assertContains(home, 'hreflang="en"')
        self.assertContains(home, 'hreflang="fr"')
        self.assertNotContains(home, 'hreflang="ru"')
        product = self.client.get(self.product.get_absolute_url())
        self.assertContains(product, '<link rel="canonical" href="http://testserver/tovar/seo-box/">')
        self.assertContains(product, '<meta property="og:title" content="Святковий бокс">')
        self.assertContains(product, 'property="og:description" content="Опис святкового боксу для столу."')
        queried = self.client.get("/?utm=ig")
        self.assertContains(queried, '<link rel="canonical" href="http://testserver/">')
        self.assertNotContains(queried, 'rel="canonical" href="http://testserver/?utm=ig"')

    def test_catalog_description(self):
        catalog = self.client.get("/katalog/")
        text = "Каталог святкових боксів і сервірування Gestia Home"
        self.assertContains(catalog, f'name="description" content="{text}"')
        category = self.client.get(self.category.get_absolute_url())
        self.assertContains(category, 'name="description" content="Святкові бокси. Gestia"')

    def test_sitemap_lists_active_product(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("/tovar/seo-box/", body)
        self.assertIn("/katalog/seo-cat/", body)
        self.assertIn("/katalog/seo-parent/", body)
        self.assertIn("/katalog/seo-child/", body)
        self.assertIn("/pro-nas/", body)
        self.assertNotIn("/tovar/seo-hidden/", body)
        self.assertNotIn("/katalog/seo-empty/", body)
        self.assertNotIn("/ru/", body)
        self.assertNotIn('hreflang="ru"', body)

    def test_robots_points_at_sitemap(self):
        response = self.client.get("/robots.txt")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")

    def test_english_page_chrome(self):
        response = self.client.get("/en/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lang="en"')
        self.assertNotContains(response, 'id="waitlist-modal"')
        self.assertContains(response, "No connection. Check your internet and try again.")
        self.assertContains(response, "Something went wrong. Please try again.")

    def test_french_page_chrome(self):
        response = self.client.get("/fr/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'lang="fr"')
        self.assertNotContains(response, 'id="waitlist-modal"')
        self.assertContains(response, "Pas de connexion. Vérifiez Internet et réessayez.")
        self.assertContains(response, "Une erreur s’est produite. Veuillez réessayer.")
