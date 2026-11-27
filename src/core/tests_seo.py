import json
import re
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.models import HomeCollection, SiteSettings
from src.core.seo import DESCRIPTION_MAX, TITLE_MAX, clip_text


def _ld(response):
    chunks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        response.content.decode(),
        flags=re.DOTALL,
    )
    return [json.loads(chunk) for chunk in chunks]


def _types(data):
    found = set()

    def walk(node):
        if isinstance(node, dict):
            kind = node.get("@type")
            if isinstance(kind, str):
                found.add(kind)
            elif isinstance(kind, list):
                found.update(item for item in kind if isinstance(item, str))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return found


def _h1_count(response):
    return response.content.decode().lower().count("<h1")


def _meta_description(response):
    match = re.search(
        r'<meta name="description" content="([^"]*)"',
        response.content.decode(),
    )
    if match is None:
        return ""
    return match.group(1)


def _word_boundary(source, clipped):
    body = clipped[:-1]
    if not body or not source.startswith(body):
        return False
    rest = source[len(body) :]
    if not rest:
        return False
    return not (body[-1].isalnum() and rest[0].isalnum())


class SeoFixture(TestCase):
    def setUp(self):
        translation.activate("uk")
        cache.clear()
        SiteSettings.objects.update_or_create(pk=1, defaults={"en_enabled": True})
        cache.clear()
        self.category = Category.objects.create(
            slug="seo-cat",
            name_uk="Святкові бокси",
            name_en="Festive boxes",
            is_active=True,
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="SEO-1",
            slug="seo-box",
            name_uk="Святковий бокс",
            seo_description_uk="Опис святкового боксу для столу.",
            price_uah=Decimal("100.00"),
            price_eur=Decimal("2.00"),
            is_active=True,
            stock_qty=4,
        )
        self.sold_out = Product.objects.create(
            category=self.category,
            sku="SEO-0",
            slug="seo-out",
            name_uk="Немає в наявності",
            price_uah=Decimal("50.00"),
            price_eur=Decimal("1.00"),
            is_active=True,
            stock_qty=0,
        )

    def tearDown(self):
        translation.activate("uk")
        cache.clear()


class SeoHeadTests(SeoFixture):
    def test_home_hreflang_is_absolute_without_russian(self):
        home = self.client.get("/")
        self.assertContains(home, '<link rel="canonical" href="http://testserver/">')
        self.assertContains(home, 'hreflang="uk" href="http://testserver/"')
        self.assertContains(home, 'hreflang="en" href="http://testserver/en/"')
        self.assertContains(home, 'hreflang="fr" href="http://testserver/fr/"')
        self.assertContains(home, 'hreflang="x-default" href="http://testserver/"')
        self.assertNotContains(home, 'hreflang="ru"')
        self.assertContains(home, 'property="og:locale" content="uk_UA"')
        french = self.client.get("/fr/")
        self.assertContains(french, 'property="og:locale" content="fr_FR"')
        self.assertContains(french, '"inLanguage":["uk-UA","en-US","fr-FR"]')
        self.assertContains(home, 'property="og:type" content="website"')
        self.assertContains(home, 'name="twitter:card" content="summary_large_image"')
        self.assertContains(home, 'property="og:image" content="http://testserver/')
        self.assertContains(home, "og-default.jpg")
        self.assertContains(home, 'property="og:image:width" content="1200"')
        self.assertContains(home, 'property="og:image:height" content="630"')
        self.assertContains(home, 'property="og:image:type" content="image/jpeg"')
        self.assertContains(home, "/chrome.css?v=")
        self.assertNotContains(home, "css/reset.css")
        self.assertNotContains(home, "css/variables.css")
        self.assertEqual(_h1_count(home), 1)
        self.assertNotContains(home, "FAQPage")
        self.assertNotContains(home, "itemprop")
        self.assertNotContains(home, "itemscope")

    def test_catalog_filter_and_page_canonical(self):
        filtered = self.client.get("/katalog/?sort=price&utm_source=ig")
        self.assertContains(filtered, '<link rel="canonical" href="http://testserver/katalog/">')
        self.assertContains(filtered, 'property="og:url" content="http://testserver/katalog/"')
        self.assertContains(filtered, 'name="robots" content="noindex,follow"')
        self.assertNotContains(filtered, 'href="http://testserver/katalog/?sort=price')
        self.assertNotContains(filtered, 'hreflang="uk"')

        queried = self.client.get("/katalog/?q=box")
        self.assertContains(queried, 'name="robots" content="noindex,follow"')
        self.assertContains(queried, 'href="http://testserver/katalog/"')

        for index in range(12):
            Product.objects.create(
                category=self.category,
                sku=f"SEO-P{index}",
                slug=f"seo-p-{index}",
                name_uk=f"Бокс {index}",
                name_en=f"Box {index}",
                price_uah=Decimal("10.00"),
                price_eur=Decimal("1.00"),
                is_active=True,
                stock_qty=1,
            )
        second = self.client.get("/katalog/seo-cat/?page=2")
        self.assertContains(second, 'rel="canonical" href="http://testserver/katalog/seo-cat/?page=2"')
        self.assertContains(second, 'hreflang="uk" href="http://testserver/katalog/seo-cat/?page=2"')
        self.assertContains(second, 'hreflang="en" href="http://testserver/en/katalog/seo-cat/?page=2"')
        self.assertContains(second, 'hreflang="fr" href="http://testserver/fr/katalog/seo-cat/?page=2"')
        self.assertContains(second, 'hreflang="x-default" href="http://testserver/katalog/seo-cat/?page=2"')
        self.assertContains(second, "сторінка 2")
        self.assertNotContains(second, "noindex")
        self.assertNotContains(self.client.get("/katalog/seo-cat/"), "сторінка 2")
        stale = self.client.get("/katalog/?page=2")
        self.assertRedirects(stale, "/katalog/", fetch_redirect_response=False)
        stale_filters = self.client.get("/katalog/?page=99&sort=name", HTTP_HX_REQUEST="true")
        self.assertEqual(stale_filters.status_code, 200)
        self.assertEqual(stale_filters["HX-Push-Url"], "/katalog/?sort=name")

        first = self.client.get("/katalog/?page=1&utm_source=ig")
        self.assertContains(first, 'rel="canonical" href="http://testserver/katalog/"')
        self.assertNotContains(first, 'href="http://testserver/katalog/?page=1')
        self.assertNotContains(first, 'hreflang="uk" href="http://testserver/katalog/?utm_source')
        self.assertEqual(_h1_count(self.client.get("/katalog/")), 1)
        self.assertEqual(_h1_count(self.client.get(self.category.get_absolute_url())), 1)

    def test_private_pages_are_noindex_without_hreflang(self):
        cart = self.client.get("/koshik/")
        self.assertContains(cart, 'name="robots" content="noindex,follow"')
        self.assertNotContains(cart, 'hreflang="en"')
        self.assertEqual(_h1_count(cart), 1)

    @override_settings(DEBUG=False)
    def test_not_found_is_noindex(self):
        missing = self.client.get("/nesnuyucha-storinka/")
        self.assertContains(missing, 'name="robots" content="noindex,follow"', status_code=404)
        self.assertNotContains(missing, 'hreflang="uk"', status_code=404)
        self.assertEqual(_h1_count(missing), 1)

    def test_long_copy_is_clipped_without_changing_short_titles(self):
        self.assertEqual(clip_text("Gestia Home", 60), "Gestia Home")
        long_title = "Святковий бокс для сервірування святкового столу вдома від Gestia Home сьогодні"
        self.product.seo_title_uk = long_title
        self.product.seo_description_uk = ("Опис святкового боксу для столу. " * 12).strip()
        self.product.save(update_fields=["seo_title_uk", "seo_description_uk"])
        page = self.client.get(self.product.get_absolute_url())
        title = re.search(r"<title>(.*?)</title>", page.content.decode()).group(1)
        description = re.search(r'name="description" content="(.*?)"', page.content.decode()).group(1)
        self.assertLessEqual(len(title), 60)
        self.assertLessEqual(len(description), 160)
        self.assertNotEqual(title, long_title)
        self.assertEqual(_h1_count(page), 1)

    def test_product_meta_description_is_non_empty(self):
        bare = Product.objects.create(
            category=self.category,
            sku="SEO-BARE",
            slug="seo-bare",
            name_uk="Порожній бокс",
            name_en="Empty box",
            price_uah=Decimal("1500.00"),
            price_eur=Decimal("30.00"),
            is_active=True,
            stock_qty=2,
        )
        uk = _meta_description(self.client.get(bare.get_absolute_url()))
        self.assertEqual(uk, "Порожній бокс. Святкові бокси. Gestia")
        self.assertNotIn("₴", uk)
        self.assertNotIn("<", uk)

        bare.description_uk = "<p>Короткий <strong>опис</strong>&nbsp;боксу</p>"
        bare.save(update_fields=["description_uk"])
        described = _meta_description(self.client.get(bare.get_absolute_url()))
        self.assertEqual(described, "Короткий опис боксу")

        bare.seo_description_uk = "<p>SEO <em>текст</em> картки</p>"
        bare.save(update_fields=["seo_description_uk"])
        self.assertEqual(
            _meta_description(self.client.get(bare.get_absolute_url())),
            "SEO текст картки",
        )

        parent = Category.objects.create(slug="seo-parent", name_uk="Декор", name_en="Decor", is_active=True)
        child = Category.objects.create(
            slug="seo-child",
            name_uk="Свічки",
            name_en="Candles",
            parent=parent,
            is_active=True,
        )
        self.assertEqual(
            _meta_description(self.client.get(child.get_absolute_url())),
            "Свічки. Декор. Gestia",
        )
        self.assertEqual(
            _meta_description(self.client.get(self.category.get_absolute_url())),
            "Святкові бокси. Gestia",
        )
        bare.seo_description_uk = ""
        bare.description_uk = ""
        bare.save(update_fields=["seo_description_uk", "description_uk"])
        self.assertEqual(
            _meta_description(self.client.get("/en/tovar/seo-bare/")),
            "Empty box. Festive boxes. Gestia",
        )
        self.assertEqual(
            _meta_description(self.client.get("/en/katalog/seo-child/")),
            "Candles. Decor. Gestia",
        )

    def test_clip_text_cuts_at_word_boundary(self):
        source = "Альфа бета гамма дельта"
        self.assertEqual(clip_text(source, 16), "Альфа бета…")
        self.assertEqual(clip_text(source, 17), "Альфа бета гамма…")
        self.assertEqual(clip_text("Коротко надзвичайнодовгеслово", 24), "Коротко…")
        self.assertEqual(clip_text("<p>Альфа <b>бета</b> гамма дельта</p>", 16), "Альфа бета…")
        self.assertNotIn("<", clip_text("<p>Альфа <b>бета</b></p>", 40))
        self.assertEqual(clip_text("Gestia", TITLE_MAX), "Gestia")

        long_title = ("Святковий " * 12).strip()
        long_description = ("Опис товару " * 30).strip()
        self.product.seo_title_uk = long_title
        self.product.seo_description_uk = long_description
        self.product.save(update_fields=["seo_title_uk", "seo_description_uk"])
        page = self.client.get(self.product.get_absolute_url())
        title = re.search(r"<title>(.*?)</title>", page.content.decode()).group(1)
        description = _meta_description(page)
        self.assertLessEqual(len(title), TITLE_MAX)
        self.assertLessEqual(len(description), DESCRIPTION_MAX)
        self.assertTrue(title.endswith("…"))
        self.assertTrue(description.endswith("…"))
        self.assertTrue(_word_boundary(long_title, title))
        self.assertTrue(_word_boundary(long_description, description))
        self.assertEqual(clip_text(long_title, TITLE_MAX), title)
        self.assertEqual(clip_text(long_description, DESCRIPTION_MAX), description)


class SeoCrawlTests(SeoFixture):
    def test_robots_lists_private_paths_and_real_filters(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        body = response.content.decode()
        self.assertIn("User-agent: *\nAllow: /\n", body)
        for path in (
            "/koshik/",
            "/zamovlennia/",
            "/thank-you/",
            "/diakuiemo/",
            "/obrane/",
            "/zayavka/",
            "/zamovyty-odrazu/",
            "/i18n/",
            "/tinymce/",
            "/healthz/",
        ):
            self.assertIn(f"Disallow: {path}\n", body)
            self.assertIn(f"Disallow: /en{path}\n", body)
            self.assertIn(f"Disallow: /fr{path}\n", body)
        for key in ("q", "in_stock", "category", "style", "color"):
            self.assertIn(f"Disallow: /*?*{key}=\n", body)
        self.assertIn("Disallow: /*?*utm_\n", body)
        self.assertIn("Disallow: /katalog/pidkazky/\n", body)
        self.assertIn("Disallow: /en/katalog/pidkazky/\n", body)
        self.assertIn("Disallow: /fr/katalog/pidkazky/\n", body)
        suggest = self.client.get("/katalog/pidkazky/?q=ab")
        self.assertEqual(suggest.status_code, 200)
        self.assertEqual(suggest["X-Robots-Tag"], "noindex")
        self.assertIn("Sitemap: http://testserver/sitemap.xml\n", body)
        self.assertNotIn("theme.css", body)
        self.assertNotIn("/admin", body)

    @override_settings(SITE_URL="https://gestia.example/")
    def test_sitemap_and_robots_use_site_url(self):
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Sitemap: https://gestia.example/sitemap.xml")
        sitemap = self.client.get("/sitemap.xml")
        self.assertContains(sitemap, "https://gestia.example/")
        self.assertContains(sitemap, "https://gestia.example/en/")
        self.assertContains(sitemap, "https://gestia.example/fr/")
        self.assertContains(sitemap, 'hreflang="x-default"')
        self.assertNotContains(sitemap, "http://testserver/")
        self.assertNotContains(sitemap, 'hreflang="ru"')

    @override_settings(SITE_URL="")
    def test_sitemap_falls_back_to_request_host(self):
        Category.objects.create(slug="seo-empty", name_uk="Порожня", is_active=True)
        sitemap = self.client.get("/sitemap.xml")
        self.assertContains(sitemap, "http://testserver/tovar/seo-box/")
        self.assertContains(sitemap, "http://testserver/en/tovar/seo-box/")
        self.assertContains(sitemap, "http://testserver/fr/tovar/seo-box/")
        self.assertContains(sitemap, "http://testserver/katalog/seo-cat/")
        self.assertNotContains(sitemap, "/katalog/seo-empty/")
        empty = self.client.get("/katalog/seo-empty/")
        self.assertContains(empty, 'name="robots" content="noindex,follow"')

    def test_llms_lists_active_categories_and_legacy_path_redirects(self):
        boxes = Category.objects.create(
            slug="llms-boxes",
            name_uk="Бокси для столу",
            name_en="Table boxes",
            is_active=True,
        )
        Category.objects.create(slug="llms-empty", name_uk="Порожня полиця", is_active=True)
        Category.objects.create(slug="llms-hidden", name_uk="Прихована категорія", is_active=False)
        Product.objects.create(
            category=boxes,
            sku="LLMS-1",
            slug="llms-standalone",
            name_uk="Окремий бокс",
            name_en="Standalone box",
            price_uah=Decimal("10.00"),
            price_eur=Decimal("1.00"),
            is_active=True,
            stock_qty=1,
        )
        page = self.client.get("/llms.txt")
        self.assertEqual(page.status_code, 200)
        self.assertIn("charset=utf-8", page["Content-Type"])
        self.assertTrue(page["Content-Type"].startswith("text/plain"))
        body = page.content.decode()
        self.assertTrue(body.startswith("# Gestia\n"))
        self.assertIn("http://testserver/katalog/llms-boxes/", body)
        self.assertIn("http://testserver/en/katalog/llms-boxes/", body)
        self.assertIn("http://testserver/fr/katalog/llms-boxes/", body)
        self.assertIn("Бокси для столу", body)
        self.assertIn("Table boxes", body)
        self.assertIn("http://testserver/tovar/llms-standalone/", body)
        self.assertIn("/fr/koshik/", body)
        self.assertIn("http://testserver/fr/katalog/", body)
        self.assertNotIn("llms-empty", body)
        self.assertNotIn("llms-hidden", body)
        self.assertNotIn("Прихована категорія", body)
        self.assertIn("http://testserver/dostavka-ta-oplata/", body)
        self.assertIn("http://testserver/en/pro-nas/", body)
        self.assertIn("http://testserver/fr/pro-nas/", body)
        self.assertIn("http://testserver/aktualni-pytannia/", body)
        self.assertIn("http://testserver/en/aktualni-pytannia/", body)
        self.assertIn("http://testserver/fr/aktualni-pytannia/", body)
        linked = Product.objects.create(
            category=boxes,
            sku="LLMS-2",
            slug="llms-linked",
            name_uk="Прив’язаний бокс",
            price_uah=Decimal("12.00"),
            price_eur=Decimal("1.00"),
            is_active=True,
            stock_qty=1,
        )
        HomeCollection.objects.create(
            slug="llms-col",
            title_uk="Квітка",
            title_en="Flower",
            title_fr="Fleur",
            product=linked,
            is_active=True,
        )
        HomeCollection.objects.create(slug="llms-hidden-col", title_uk="Прихована колекція", is_active=False)
        listed = self.client.get("/llms.txt").content.decode()
        self.assertIn("http://testserver/kolektsiia/llms-col/", listed)
        self.assertIn("http://testserver/en/kolektsiia/llms-col/", listed)
        self.assertIn("http://testserver/fr/kolektsiia/llms-col/", listed)
        self.assertIn("Квітка", listed)
        self.assertIn("Flower", listed)
        self.assertNotIn("llms-hidden-col", listed)
        self.assertNotIn("/tovar/llms-linked/", listed)
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("http://testserver/kolektsiia/llms-col/", sitemap)
        self.assertRegex(
            sitemap,
            r"<loc>http://testserver/katalog/</loc>\s*<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
        )
        self.assertRegex(
            sitemap,
            r"<loc>http://testserver/kolektsiia/llms-col/</loc>\s*<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
        )
        legacy = self.client.get("/llm.txt")
        self.assertEqual(legacy.status_code, 301)
        self.assertEqual(legacy["Location"], "/llms.txt")

    @override_settings(ADMIN_URL="secret-panel-xyz/")
    def test_secret_admin_prefix_stays_out_of_public_text(self):
        robots = self.client.get("/robots.txt")
        llms = self.client.get("/llms.txt")
        self.assertNotContains(robots, "secret-panel-xyz")
        self.assertNotContains(llms, "secret-panel-xyz")
        admin = self.client.get("/secret-panel-xyz/")
        self.assertIn("noindex", admin["X-Robots-Tag"])
        self.assertIn("nofollow", admin["X-Robots-Tag"])


class SeoStructuredDataTests(SeoFixture):
    def test_home_has_organization_and_website_only(self):
        payloads = _ld(self.client.get("/"))
        self.assertEqual(len(payloads), 1)
        kinds = _types(payloads[0])
        self.assertIn("Organization", kinds)
        self.assertIn("WebSite", kinds)
        self.assertNotIn("Product", kinds)
        self.assertNotIn("FAQPage", kinds)
        self.assertNotIn("AggregateRating", kinds)

    def test_product_jsonld_has_offer_stock_and_breadcrumbs(self):
        page = self.client.get(self.product.get_absolute_url())
        payloads = _ld(page)
        self.assertEqual(len(payloads), 1)
        raw = page.content.decode()
        self.assertNotIn("FAQPage", raw)
        self.assertNotIn("AggregateRating", raw)
        self.assertNotIn("itemprop", raw)
        kinds = _types(payloads[0])
        self.assertIn("Product", kinds)
        self.assertIn("Offer", kinds)
        self.assertIn("BreadcrumbList", kinds)
        self.assertIn("Organization", kinds)
        self.assertIn("WebSite", kinds)
        self.assertIn("https://schema.org/InStock", raw)
        self.assertIn('"brand":{"@type":"Brand","name":"Gestia Home"}', raw)
        self.assertIn('"priceCurrency":"UAH"', raw)
        self.assertIn('"sku":"SEO-1"', raw)
        self.assertIn("http://testserver/tovar/seo-box/", raw)

        sold = self.client.get(self.sold_out.get_absolute_url())
        sold_raw = sold.content.decode()
        self.assertIn("https://schema.org/OutOfStock", sold_raw)
        self.assertNotIn("https://schema.org/InStock", sold_raw)

    def test_collection_landing_is_the_product_url(self):
        HomeCollection.objects.create(
            slug="seo-col",
            title_uk="Квітка",
            title_en="Flower",
            title_fr="Fleur",
            product=self.product,
            is_active=True,
        )
        sitemap = self.client.get("/sitemap.xml").content.decode()
        self.assertNotIn("/tovar/seo-box/", sitemap)
        self.assertIn("http://testserver/kolektsiia/seo-col/", sitemap)
        self.assertIn("/tovar/seo-out/", sitemap)
        gone = self.client.get(self.product.get_absolute_url())
        self.assertEqual(gone.status_code, 301)
        self.assertEqual(gone["Location"], "/kolektsiia/seo-col/")

        page = self.client.get("/kolektsiia/seo-col/")
        self.assertContains(page, 'property="og:type" content="product"')
        raw = page.content.decode()
        self.assertNotIn("/tovar/seo-box/", raw)
        payloads = _ld(page)
        self.assertIn("Product", _types(payloads[0]))
        self.assertIn("Offer", _types(payloads[0]))
        self.assertIn("BreadcrumbList", _types(payloads[0]))
        product = next(
            node
            for node in payloads[0]["@graph"]
            if node.get("@type") == "Product"
        )
        self.assertEqual(product["url"], "http://testserver/kolektsiia/seo-col/")
        self.assertEqual(product["name"], "Квітка")
        self.assertEqual(product["offers"]["url"], "http://testserver/kolektsiia/seo-col/")
        self.assertEqual(product["brand"]["name"], "Gestia Home")

        self.assertContains(
            self.client.get("/en/kolektsiia/seo-col/"),
            "<title>Collection «Flower» — Gestia Home</title>",
        )
        self.assertContains(
            self.client.get("/fr/kolektsiia/seo-col/"),
            "<title>Collection «Fleur» — Gestia Home</title>",
        )
        self.assertContains(page, "<title>Колекція «Квітка» — Gestia Home</title>")
