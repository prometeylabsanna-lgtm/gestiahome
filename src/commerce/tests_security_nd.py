from decimal import Decimal
from urllib.parse import urlsplit

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product


class WishlistToggleNextSecurityTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        category = Category.objects.create(slug="sec-wish-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="SEC-WISH-1",
            slug="sec-wish-1",
            name_uk="Тестовий товар",
            price_uah=Decimal("1000"),
            price_eur=Decimal("25"),
            stock_qty=5,
        )
        self.url = reverse("wishlist_toggle")

    def _post_next(self, next_value: str):
        return self.client.post(
            self.url,
            {"sku": self.product.sku, "next": next_value},
        )

    def _assert_not_external(self, location: str):
        parts = urlsplit(location)
        self.assertFalse(parts.scheme, location)
        self.assertFalse(parts.netloc, location)
        self.assertTrue(location.startswith("/"), location)
        self.assertFalse(location.startswith("//"), location)
        self.assertNotIn("evil.example", location)

    def test_external_https_next_is_rejected(self):
        response = self._post_next("https://evil.example")
        self.assertEqual(response.status_code, 302)
        location = response["Location"]
        self._assert_not_external(location)
        self.assertIn(
            location,
            {"/", self.product.get_absolute_url()},
        )

    def test_protocol_relative_and_backslash_next_not_external(self):
        for raw in ("//evil.example", r"/\\evil"):
            with self.subTest(raw=raw):
                response = self._post_next(raw)
                self.assertEqual(response.status_code, 302)
                self._assert_not_external(response["Location"])

    def test_safe_internal_next_kept(self):
        response = self._post_next("/obrane/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/obrane/")


class CartNeverCacheSecurityTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        category = Category.objects.create(slug="sec-cache-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="SEC-CACHE-1",
            slug="sec-cache-1",
            name_uk="Тестовий товар",
            price_uah=Decimal("1000"),
            price_eur=Decimal("25"),
            stock_qty=5,
        )

    def _assert_never_cache(self, response):
        cache_control = response.get("Cache-Control", "")
        self.assertIn("no-store", cache_control)
        self.assertIn("private", cache_control)

    def test_cart_panel_never_cache(self):
        response = self.client.get(reverse("cart_panel"))
        self.assertEqual(response.status_code, 200)
        self._assert_never_cache(response)

    def test_cart_page_never_cache(self):
        response = self.client.get(reverse("cart"))
        self.assertEqual(response.status_code, 200)
        self._assert_never_cache(response)

    def test_cart_add_htmx_never_cache(self):
        response = self.client.post(
            reverse("cart_add"),
            {"sku": self.product.sku, "qty": "1"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self._assert_never_cache(response)

    def test_cart_add_htmx_panel_never_cache(self):
        response = self.client.post(
            reverse("cart_add"),
            {
                "sku": self.product.sku,
                "qty": "1",
                "panel": "1",
                "panel_sku": self.product.sku,
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self._assert_never_cache(response)

    def test_cart_update_htmx_never_cache(self):
        session = self.client.session
        session["cart"] = {self.product.sku: 1}
        session.save()
        response = self.client.post(
            reverse("cart_update"),
            {"sku": self.product.sku, "qty": "2"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self._assert_never_cache(response)

    def test_cart_update_htmx_panel_never_cache(self):
        session = self.client.session
        session["cart"] = {self.product.sku: 1}
        session.save()
        response = self.client.post(
            reverse("cart_update"),
            {
                "sku": self.product.sku,
                "qty": "2",
                "panel": "1",
                "panel_sku": self.product.sku,
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self._assert_never_cache(response)
