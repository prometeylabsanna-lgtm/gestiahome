import re
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.models import Order
from src.core.ratelimit import HONEYPOT_FIELD


def _hidden(html: str, name: str) -> str:
    match = re.search(
        rf'<input[^>]*name="{name}"[^>]*value="([^"]*)"',
        html,
    )
    if not match:
        match = re.search(
            rf'<input[^>]*value="([^"]*)"[^>]*name="{name}"',
            html,
        )
    assert match, f"hidden {name} missing"
    return match.group(1)


class CheckoutNdTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.category = Category.objects.create(slug="nd-co-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=self.category,
            sku="ND-CO-1",
            slug="nd-co-1",
            name_uk="Бокс «Різдвяний Шишки»",
            price_uah=Decimal("4980"),
            price_eur=Decimal("100"),
            stock_qty=10,
        )
        self.extra = Product.objects.create(
            category=self.category,
            sku="ND-CO-2",
            slug="nd-co-2",
            name_uk="Бокс «Газетний»",
            price_uah=Decimal("3200"),
            price_eur=Decimal("70"),
            stock_qty=10,
        )

    def tearDown(self):
        translation.activate("uk")
        cache.clear()

    def _fill(self, **items):
        session = self.client.session
        session["cart"] = items or {"ND-CO-1": 1, "ND-CO-2": 2}
        session["currency"] = "uah"
        session.save()

    def _page(self):
        self._fill()
        return self.client.get(reverse("checkout"))

    def _payload(self, html=None, **extra):
        if html is None:
            html = self._page().content.decode()
        data = {
            "name": "Оля",
            "phone": "+380671112233",
            "email": "olya@example.com",
            "delivery_method": Order.Delivery.BRANCH,
            "city": "Київ",
            "branch": "Відділення 12",
            "payment_method": Order.Payment.ON_DELIVERY,
            "consent": "on",
            "cart_sig": _hidden(html, "cart_sig"),
            "idem": _hidden(html, "idem"),
        }
        data.update(extra)
        return data

    def test_checkout_page_renders_nd_markup(self):
        response = self._page()
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertContains(response, "css/nd/checkout.css")
        self.assertContains(response, "js/nd/checkout-label.js")
        self.assertContains(response, "js/pages/checkout.js")
        self.assertNotContains(response, "css/pages/checkout.css")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertIn(f'name="{HONEYPOT_FIELD}"', html)
        self.assertIn('name="cart_sig"', html)
        self.assertIn('name="idem"', html)
        for name in (
            "name",
            "phone",
            "email",
            "delivery_method",
            "city",
            "branch",
            "house",
            "apartment",
            "payment_method",
            "consent",
        ):
            self.assertIn(f'name="{name}"', html)
        self.assertIn("data-np-ship", html)
        self.assertIn("data-np-city", html)
        self.assertIn("data-np-branch", html)
        self.assertIn("data-np-street-line", html)
        self.assertIn("data-np-house", html)
        self.assertIn("data-np-apartment", html)
        self.assertIn("data-validate-form", html)
        self.assertIn('name="delivery_method" value="np_branch"', html)
        self.assertIn('name="delivery_method" value="np_locker"', html)
        self.assertIn('name="delivery_method" value="np_courier"', html)
        self.assertIn('name="payment_method" value="card"', html)
        self.assertIn('name="payment_method" value="on_delivery"', html)
        self.assertContains(response, "Нова пошта (відділення)")
        self.assertContains(response, "Онлайн карткою на сайті")
        self.assertContains(response, 'type="checkbox" name="consent"')
        self.assertContains(response, "Оформити замовлення")
        self.assertContains(response, "data-label-pay")
        self.assertContains(response, "Підтвердження замовлення та деталі оплати надсилаються після оформлення")
        self.assertContains(response, "Бокс «Різдвяний Шишки»")
        self.assertContains(response, "× 1")
        self.assertContains(response, "× 2")
        self.assertContains(response, "11 380 UAH")
        self.assertNotContains(response, "₴ 11 380 грн")
        self.assertNotContains(response, "Укрпошта")
        self.assertNotContains(response, "Коментар")

    def test_empty_cart_redirects_to_cart(self):
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("cart"))

    @override_settings(NOVA_POSHTA_API_KEY="", DEBUG=True)
    def test_valid_post_creates_order_and_clears_cart(self):
        page = self._page()
        before = Order.objects.count()
        response = self.client.post(reverse("checkout"), self._payload(page.content.decode()))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/thank-you/", response["Location"])
        self.assertEqual(Order.objects.count(), before + 1)
        order = Order.objects.latest("id")
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total, Decimal("11380"))
        self.assertEqual(order.delivery_address, "Київ, Відділення 12")
        self.assertEqual(self.client.session.get("cart"), {})

    @override_settings(NOVA_POSHTA_API_KEY="", DEBUG=True)
    def test_same_idem_does_not_duplicate(self):
        page = self._page()
        payload = self._payload(page.content.decode(), idem="nd-co-idem-1")
        first = self.client.post(reverse("checkout"), payload)
        second = self.client.post(reverse("checkout"), payload)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(first["Location"], second["Location"])
        self.assertEqual(Order.objects.count(), 1)

    def test_invalid_post_keeps_errors(self):
        page = self._page()
        response = self.client.post(
            reverse("checkout"),
            self._payload(
                page.content.decode(),
                name="",
                email="bad",
                consent="",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, 'data-error-for="name"')
        self.assertContains(response, 'data-error-for="email"')
        self.assertContains(response, 'data-error-for="consent"')
        self.assertContains(response, "css/nd/checkout.css")
        self.assertEqual(self.client.session["cart"]["ND-CO-1"], 1)
