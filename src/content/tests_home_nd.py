from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.models import HomeBlock, HomeCollection
from src.content.models_home_slots import HomePopularSlot


def _block(key, **values):
    block, _created = HomeBlock.objects.get_or_create(key=key, defaults=values)
    for name, value in values.items():
        setattr(block, name, value)
    block.save()
    return block


class HomeNdRenderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.hero = _block(
            "hero",
            title_uk="Art of modern hospitality",
            text_uk="Святкові бокси для самостійного декорування столу",
            cta_uk="Перейти до каталогу",
            sort=1,
        )
        self.collections = _block(
            "collections",
            title_uk="Різдвяна колекція святкових боксів",
            link_uk="Традиції починаються зі столу",
            cta_uk="Дізнатись детальніше",
            sort=2,
        )
        self.popular_block = _block(
            "popular",
            title_uk="Популярні товари",
            cta_uk="Перейти до каталогу",
            sort=4,
        )
        self.category = Category.objects.create(
            slug="rizdvyani-boksy",
            name_uk="Різдвяні бокси",
            is_active=True,
        )
        self.active = HomeCollection.objects.create(
            block=self.collections,
            slug="nd-kvitka-dusha",
            label_uk="Колекція",
            title_uk="Квітка-душа",
            text_uk="<p>Текст колекції</p>",
            category=self.category,
            is_active=True,
            sort=1,
        )
        HomeCollection.objects.create(
            block=self.collections,
            label_uk="Колекція",
            title_uk="Прихована",
            is_active=False,
            sort=2,
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="NDPOP1",
            slug="nd-pop-1",
            name_uk="Бокс тест",
            price_uah="100",
            price_eur="3",
            is_active=True,
            is_popular=True,
        )
        HomePopularSlot.objects.create(
            block=self.popular_block,
            product=self.product,
            sort=1,
        )

    def test_hero_shows_cms_slogan(self):
        page = self.client.get("/")
        self.assertContains(page, "Art of modern hospitality")
        self.assertContains(page, "Святкові бокси для самостійного декорування столу")
        self.assertContains(page, "nd/logo-gestia-light.svg")
        self.assertContains(page, 'class="nd-hero')

    def test_collections_render_from_cms(self):
        page = self.client.get("/")
        self.assertContains(page, "Різдвяна колекція святкових боксів")
        self.assertContains(page, "Квітка-душа")
        self.assertContains(page, "Дізнатись детальніше")
        self.assertContains(page, reverse("collection", kwargs={"slug": "nd-kvitka-dusha"}))
        self.assertNotContains(page, "Прихована")

    def test_collection_without_slug_links_to_catalog(self):
        self.active.slug = None
        self.active.category = None
        self.active.save(update_fields=["slug", "category"])
        page = self.client.get("/")
        self.assertContains(page, reverse("catalog"))
        self.assertContains(page, "Квітка-душа")

    def test_popular_shows_products_and_wishlist(self):
        page = self.client.get("/")
        self.assertContains(page, "Популярні товари")
        self.assertContains(page, "Бокс тест")
        self.assertContains(page, 'class="wish-toggle wish-toggle--nd"')
        self.assertContains(page, 'name="sku" value="NDPOP1"')
        self.assertContains(page, 'name="variant" value="nd"')
        self.assertContains(page, reverse("wishlist_toggle"))
        self.assertContains(page, 'viewBox="0 0 24 24"')
        self.assertContains(
            page,
            'd="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"',
        )
        self.assertNotContains(page, 'class="cats"')
        self.assertNotContains(page, 'class="benefits"')
        self.assertNotContains(page, 'class="reviews"')
        self.assertNotContains(page, 'class="callback"')

    def test_wishlist_toggle_nd_returns_svg_variant(self):
        added = self.client.post(
            reverse("wishlist_toggle"),
            {"sku": "NDPOP1", "variant": "nd"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(added.status_code, 200)
        body = added.content.decode()
        self.assertIn('class="wish-toggle wish-toggle--nd"', body)
        self.assertIn('name="variant" value="nd"', body)
        self.assertIn("<svg", body)
        self.assertIn('viewBox="0 0 24 24"', body)
        self.assertIn("is-on", body)
        self.assertIn('fill="currentColor"', body)
        removed = self.client.post(
            reverse("wishlist_toggle"),
            {"sku": "NDPOP1", "variant": "nd"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(removed.status_code, 200)
        out = removed.content.decode()
        self.assertIn('class="wish-toggle wish-toggle--nd"', out)
        self.assertIn("<svg", out)
        self.assertIn('fill="none"', out)
        self.assertNotIn("is-on", out)
