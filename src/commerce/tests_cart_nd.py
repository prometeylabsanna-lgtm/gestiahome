import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.content.models import HomeCollection


class CartNdTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.category = Category.objects.create(slug="nd-cart-cat", name_uk="Каталог")
        self.main = Product.objects.create(
            category=self.category,
            sku="BOX-1",
            slug="box-1",
            name_uk="Бокс «Різдвяний Шишки»",
            price_uah=Decimal("4980"),
            price_eur=Decimal("100"),
            stock_qty=10,
        )
        self.extra = Product.objects.create(
            category=self.category,
            sku="BOX-2",
            slug="box-2",
            name_uk="Бокс «Газетний»",
            price_uah=Decimal("3200"),
            price_eur=Decimal("70"),
            stock_qty=10,
        )
        self.addon = Product.objects.create(
            category=self.category,
            sku="ADDON-1",
            slug="addon-1",
            name_uk="Лляні серветки",
            price_uah=Decimal("890"),
            price_eur=Decimal("20"),
            stock_qty=10,
        )
        self.addon2 = Product.objects.create(
            category=self.category,
            sku="ADDON-2",
            slug="addon-2",
            name_uk="Кільця для серветок",
            price_uah=Decimal("650"),
            price_eur=Decimal("15"),
            stock_qty=10,
        )
        self.collection = HomeCollection.objects.create(
            slug="rizdvianyi-cart-nd",
            title_uk="Різдвяний",
            product=self.main,
            is_active=True,
            sort=1,
        )
        self.collection.addons.add(self.addon, self.addon2)

    def _fill(self):
        session = self.client.session
        session["cart"] = {"BOX-1": 1, "BOX-2": 2}
        session["currency"] = "uah"
        session.save()

    def test_cart_page_with_items(self):
        self._fill()
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Кошик (3)")
        self.assertContains(response, "Бокс «Різдвяний Шишки»")
        self.assertContains(response, "Бокс «Газетний»")
        self.assertContains(response, "4 980 UAH")
        self.assertContains(response, "6 400 UAH")
        self.assertContains(response, "Загальна ціна")
        self.assertContains(response, "11 380 UAH")
        self.assertContains(response, "Перейти до оформлення")
        self.assertContains(response, reverse("checkout"))
        self.assertContains(response, "Доповнити сет")
        self.assertContains(response, "Лляні серветки")
        self.assertContains(response, "css/nd/cart.css")
        self.assertContains(response, "js/nd/cart.js")
        self.assertNotContains(response, "css/pages/cart.css")
        self.assertNotContains(response, "js/pages/cart.js")

    def test_cart_empty_state(self):
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ваш кошик порожній")
        self.assertContains(response, "Перейти до каталогу")
        self.assertNotContains(response, "Загальна ціна")
        self.assertNotContains(response, "Перейти до оформлення")

    def test_cart_update_htmx_without_panel(self):
        self._fill()
        response = self.client.post(
            reverse("cart_update"),
            {"sku": "BOX-1", "qty": "2"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cart-title"')
        self.assertContains(response, "Кошик (4)")
        self.assertContains(response, "hx-swap-oob")
        self.assertNotContains(response, "nd-cart-drawer__title")
        self.assertEqual(self.client.session["cart"]["BOX-1"], 2)

    def test_cart_add_htmx_trigger(self):
        response = self.client.post(
            reverse("cart_add"),
            {"sku": "BOX-1", "qty": "1"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cart-count"')
        trigger = json.loads(response["HX-Trigger"])
        self.assertEqual(trigger["nd:cart-added"]["sku"], "BOX-1")

    def test_cart_panel_get(self):
        self._fill()
        response = self.client.get(reverse("cart_panel"), {"sku": "BOX-1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Бокс «Різдвяний Шишки»")
        self.assertContains(response, "Підсумок")
        self.assertContains(response, "11 380 UAH")
        self.assertContains(response, reverse("checkout"))
        self.assertContains(response, reverse("cart"))
        self.assertContains(response, "Доповнити сет")
        self.assertContains(response, "Лляні серветки")
        self.assertContains(response, 'role="group"')

    def test_cart_update_panel(self):
        self._fill()
        response = self.client.post(
            reverse("cart_update"),
            {"sku": "BOX-1", "qty": "3", "panel": "1", "panel_sku": "BOX-1"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nd-cart-drawer__title")
        self.assertContains(response, 'value="3"')
        self.assertEqual(self.client.session["cart"]["BOX-1"], 3)
        trigger = json.loads(response["HX-Trigger"])
        self.assertTrue(trigger.get("nd:cart-changed"))

    def test_panel_addons_toggle_added(self):
        session = self.client.session
        session["cart"] = {"BOX-1": 1, "ADDON-1": 1}
        session.save()
        response = self.client.get(reverse("cart_panel"), {"sku": "BOX-1"})
        self.assertContains(response, "Додано")
        self.assertContains(response, "is-added")
        removed = self.client.post(
            reverse("cart_update"),
            {"sku": "ADDON-1", "qty": "0", "panel": "1", "panel_sku": "BOX-1"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(removed.status_code, 200)
        self.assertNotIn("ADDON-1", self.client.session.get("cart", {}))
        self.assertContains(removed, "Додати")

    def test_suggest_from_all_collections_when_no_match(self):
        orphan = Product.objects.create(
            category=self.category,
            sku="ORPHAN",
            slug="orphan",
            name_uk="Сирота",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=5,
        )
        session = self.client.session
        session["cart"] = {"ORPHAN": 1}
        session.save()
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Доповнити сет")
        self.assertContains(response, "Лляні серветки")

    def test_base_includes_drawer_partial(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="true"')
        self.assertContains(response, 'id="nd-cart-drawer-panel"')
        self.assertContains(response, "js/nd/cart-drawer.js")
        self.assertContains(response, "css/nd/cart-drawer.css")
