from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product


class WishlistNdTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        self.category = Category.objects.create(slug="nd-wish-cat", name_uk="Каталог")
        self.p1 = Product.objects.create(
            category=self.category,
            sku="GH-01",
            slug="gh-01",
            name_uk="Бокс Великодній «Український»",
            price_uah=Decimal("8990"),
            price_eur=Decimal("200"),
            stock_qty=10,
        )
        self.p2 = Product.objects.create(
            category=self.category,
            sku="GH-02",
            slug="gh-02",
            name_uk="Бокс «Різдвяний Шишки»",
            price_uah=Decimal("4980"),
            price_eur=Decimal("100"),
            stock_qty=10,
        )
        self.p3 = Product.objects.create(
            category=self.category,
            sku="GH-06",
            slug="gh-06",
            name_uk="Бокс «Газетний»",
            price_uah=Decimal("5130"),
            price_eur=Decimal("110"),
            stock_qty=10,
        )
        self.out = Product.objects.create(
            category=self.category,
            sku="GH-04",
            slug="gh-04",
            name_uk="Бокс «Квітковий»",
            price_uah=Decimal("3500"),
            price_eur=Decimal("80"),
            stock_qty=0,
            stock_status=Product.Stock.OUT,
        )

    def _fill(self):
        session = self.client.session
        session["wishlist"] = ["GH-01", "GH-02", "GH-06", "GH-04"]
        session["currency"] = "uah"
        session.save()

    def test_wishlist_page_with_items(self):
        self._fill()
        response = self.client.get(reverse("wishlist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обране (4)")
        self.assertContains(response, "Бокс Великодній «Український»")
        self.assertContains(response, "Бокс «Різдвяний Шишки»")
        self.assertContains(response, "Бокс «Газетний»")
        self.assertContains(response, "Бокс «Квітковий»")
        self.assertContains(response, "8 990 UAH")
        self.assertContains(response, "В кошик")
        self.assertContains(response, "css/nd/wishlist.css")
        self.assertNotContains(response, "css/pages/wishlist.css")
        self.assertContains(response, reverse("home"))
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, "Видалити з обраного")
        self.assertContains(response, reverse("cart_add"))
        self.assertContains(response, 'name="sku"')
        self.assertContains(response, "GH-01")
        self.assertContains(response, "hx-post")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, "disabled")

    def test_wishlist_empty_state(self):
        response = self.client.get(reverse("wishlist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "У вас поки немає обраних товарів")
        self.assertContains(response, "Перейти до каталогу")
        self.assertContains(response, reverse("catalog"))
        self.assertNotContains(response, "В кошик")
        self.assertContains(response, "css/nd/wishlist.css")

    def test_wishlist_remove_htmx_returns_body(self):
        self._fill()
        response = self.client.post(
            reverse("wishlist_remove"),
            {"sku": "GH-01"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обране (3)")
        self.assertNotContains(response, "Бокс Великодній «Український»")
        self.assertContains(response, "Бокс «Різдвяний Шишки»")
        self.assertEqual(
            self.client.session.get("wishlist"),
            ["GH-02", "GH-06", "GH-04"],
        )

    def test_wishlist_cart_add_form(self):
        self._fill()
        response = self.client.get(reverse("wishlist"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(reverse("cart_add"), body)
        self.assertIn('hx-post="%s"' % reverse("cart_add"), body)
        self.assertIn('name="sku" value="GH-02"', body)
        self.assertIn('name="csrfmiddlewaretoken"', body)
        self.assertIn('hx-target="#cart-count"', body)
