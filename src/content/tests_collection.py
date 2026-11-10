from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.models import HomeBlock, HomeCollection
from src.content.models_menu import MenuGroup, MenuGroupItem


class CollectionPageTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.category = Category.objects.create(
            slug="svyatkovi-boksy",
            name_uk="Святкові бокси",
            is_active=True,
        )
        self.product = Product.objects.create(
            category=self.category,
            sku="COLBOX1",
            slug="col-box-1",
            name_uk="Бокс Квітка",
            price_uah=Decimal("4980"),
            price_eur=Decimal("120"),
            is_active=True,
            stock_qty=5,
        )
        self.addon = Product.objects.create(
            category=self.category,
            sku="COLADD1",
            slug="col-add-1",
            name_uk="Лляні серветки",
            price_uah=Decimal("890"),
            price_eur=Decimal("20"),
            is_active=True,
            stock_qty=5,
        )
        HomeBlock.objects.get_or_create(
            key="pdp_ship",
            defaults={"sort": 20, "title_uk": "Доставка", "text_uk": "<p>Нова пошта</p>"},
        )
        HomeBlock.objects.get_or_create(
            key="pdp_pay",
            defaults={"sort": 21, "title_uk": "Оплата", "text_uk": "<p>Картка</p>"},
        )
        self.active = HomeCollection.objects.create(
            slug="page-kvitka-dusha",
            label_uk="Колекція",
            title_uk="Квітка-душа",
            story_uk="<p>Історія квітки</p><p>Другий абзац</p>",
            box_items_uk="Вази-креманки — 2 штуки\nЖива хвоя",
            category=self.category,
            product=self.product,
            is_active=True,
            sort=1,
        )
        self.active.addons.add(self.addon)
        self.other = HomeCollection.objects.create(
            slug="page-korinnia",
            label_uk="Колекція",
            title_uk="Коріння",
            story_uk="<p>Інша історія</p>",
            is_active=True,
            sort=2,
        )
        self.inactive = HomeCollection.objects.create(
            slug="page-hidden-col",
            title_uk="Прихована",
            is_active=False,
            sort=3,
        )
        self.group = MenuGroup.objects.create(
            title_uk="Святкові бокси",
            sort=1,
            is_active=True,
            open_by_default=True,
        )
        self.menu_item = MenuGroupItem.objects.create(
            group=self.group,
            label_uk="«Квітка-душа»",
            collection=self.active,
            sort=1,
            is_active=True,
        )

    def test_active_collection_renders_200(self):
        page = self.client.get(reverse("collection", kwargs={"slug": "page-kvitka-dusha"}))
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        self.assertIn("Історія квітки", html)
        self.assertIn("Другий абзац", html)
        self.assertIn("Вази-креманки — 2 штуки", html)
        self.assertIn("Жива хвоя", html)
        self.assertIn("Коріння", html)
        self.assertIn("Доповнити сет", html)
        self.assertIn("Лляні серветки", html)
        self.assertIn('action="/koshik/dodaty/"', html)
        self.assertIn('name="sku" value="COLBOX1"', html)
        self.assertIn('name="sku" value="COLADD1"', html)
        self.assertIn("Доставка", html)
        self.assertIn("Оплата", html)
        self.assertIn("nd/collection.css", html)
        self.assertIn("Святкові бокси", html)
        self.assertIn('aria-labelledby="others-title"', html)
        self.assertIn('data-screen-label="Collection hero"', html)
        self.assertIn('data-screen-label="In the box"', html)
        self.assertIn('data-screen-label="Delivery and payment"', html)

    def test_inactive_collection_is_404(self):
        page = self.client.get(reverse("collection", kwargs={"slug": "page-hidden-col"}))
        self.assertEqual(page.status_code, 404)

    def test_cart_and_addons_hidden_without_product(self):
        self.active.product = None
        self.active.save(update_fields=["product"])
        self.active.addons.clear()
        page = self.client.get(reverse("collection", kwargs={"slug": "page-kvitka-dusha"}))
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        self.assertNotIn('name="sku" value="COLBOX1"', html)
        self.assertNotIn("Доповнити сет", html)
        self.assertIn("Що в боксі", html)

    def test_absolute_url_and_menu_point_to_collection(self):
        url = reverse("collection", kwargs={"slug": "page-kvitka-dusha"})
        self.assertEqual(self.active.get_absolute_url(), url)
        self.assertEqual(self.menu_item.get_href(), url)
        home = self.client.get(reverse("home"))
        self.assertContains(home, f'href="{url}"')
