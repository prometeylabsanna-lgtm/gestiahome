from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.models import Inquiry, Order
from src.content.models import HomeBlock
from src.core.ratelimit import HONEYPOT_FIELD

HONEYPOT_MARK = f'name="{HONEYPOT_FIELD}"'
LIMIT_ONE = {"default": {"limit": 1, "window": 600}}
TOO_MANY = "Забагато спроб. Спробуйте трохи пізніше."


def _person(**extra):
    data = {
        "name": "Оля",
        "phone": "+380671112233",
        "consent": "on",
    }
    data.update(extra)
    return data


class PublicFormGuardTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        cache.clear()
        category = Category.objects.create(slug="guard-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="GUARD",
            slug="guard-box",
            name_uk="Бокс",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=100,
        )
        HomeBlock.objects.create(key=HomeBlock.Key.CALLBACK, title_uk="Зворотний")

    def tearDown(self):
        translation.activate("uk")
        cache.clear()

    def _cart(self):
        session = self.client.session
        session["cart"] = {"GUARD": 1}
        session["currency"] = "uah"
        session.save()

    def test_honeypot_is_rendered_on_personal_forms(self):
        home = self.client.get("/")
        self.assertContains(home, HONEYPOT_MARK)
        self.assertGreaterEqual(home.content.decode().count(HONEYPOT_MARK), 2)
        product = self.client.get(self.product.get_absolute_url())
        self.assertContains(product, HONEYPOT_MARK)
        product_html = product.content.decode()
        cart_form = product_html.split('action="/koshik/dodaty/"', 1)[1].split("</form>", 1)[0]
        self.assertNotIn(HONEYPOT_MARK, cart_form)
        self._cart()
        checkout = self.client.get("/zamovlennia/")
        checkout_form = checkout.content.decode().split('action="/zamovlennia/"', 1)[1].split("</form>", 1)[0]
        self.assertIn(HONEYPOT_MARK, checkout_form)
        contact = self.client.post("/zvorotnyi-zvyazok/", {})
        self.assertContains(contact, HONEYPOT_MARK)

    def test_callback_honeypot_pretends_success(self):
        payload = _person(sku="GUARD", **{HONEYPOT_FIELD: "https://spam.example"})
        response = self.client.post("/zayavka/", payload)
        self.assertContains(response, "Дякуємо")
        self.assertEqual(Inquiry.objects.count(), 0)
        saved = self.client.post("/zayavka/", _person(sku="GUARD", **{HONEYPOT_FIELD: "   "}))
        self.assertContains(saved, "Дякуємо")
        self.assertEqual(Inquiry.objects.count(), 1)

    def test_legacy_website_honeypot_still_blocks(self):
        response = self.client.post("/zayavka/", _person(sku="GUARD", website="bot"))
        self.assertContains(response, "Дякуємо")
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_contact_honeypot_pretends_success(self):
        payload = _person(message="Привіт", **{HONEYPOT_FIELD: "bot"})
        response = self.client.post("/zvorotnyi-zvyazok/", payload)
        self.assertContains(response, "Дякуємо")
        self.assertNotContains(response, "найближчим часом")
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_home_honeypot_pretends_success(self):
        response = self.client.post("/", _person(message="Привіт", **{HONEYPOT_FIELD: "bot"}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("kind=contact", response["Location"])
        self.assertEqual(Inquiry.objects.count(), 0)
        saved = self.client.post("/", _person(message="Привіт"))
        self.assertEqual(saved.status_code, 302)
        self.assertEqual(Inquiry.objects.count(), 1)

    def test_waitlist_honeypot_pretends_success(self):
        response = self.client.post(
            "/svyatkovi-boksy/",
            {"email": "guest@example.com", "consent": "on", HONEYPOT_FIELD: "bot"},
            HTTP_HX_REQUEST="true",
        )
        self.assertContains(response, "data-waitlist-success")
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_buy_now_honeypot_pretends_success(self):
        payload = _person(address="Київ", sku="GUARD", **{HONEYPOT_FIELD: "bot"})
        response = self.client.post("/zamovyty-odrazu/", payload)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/thank-you/", response["Location"])
        self.assertNotIn("number=", response["Location"])
        self.assertEqual(Order.objects.count(), 0)
        hx = self.client.post("/zamovyty-odrazu/", payload, HTTP_HX_REQUEST="true")
        self.assertEqual(hx.status_code, 200)
        self.assertIn("/thank-you/", hx["HX-Redirect"])
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_honeypot_pretends_success(self):
        self._cart()
        response = self.client.post(
            "/zamovlennia/",
            _person(
                email="olya@example.com",
                delivery_method=Order.Delivery.BRANCH,
                address="Відділення 12",
                payment_method=Order.Payment.ON_DELIVERY,
                **{HONEYPOT_FIELD: "bot"},
            ),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/thank-you/", response["Location"])
        self.assertNotIn("number=", response["Location"])
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.client.session["cart"], {"GUARD": 1})

    @override_settings(RATE_LIMITS=LIMIT_ONE)
    def test_callback_returns_429_without_saving(self):
        first = self.client.post("/zayavka/", _person(sku="GUARD"))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(Inquiry.objects.count(), 1)
        blocked = self.client.post("/zayavka/", _person(sku="GUARD"))
        self.assertContains(blocked, TOO_MANY, status_code=429)
        self.assertContains(blocked, 'name="name"', status_code=429)
        self.assertEqual(Inquiry.objects.count(), 1)

    @override_settings(RATE_LIMITS=LIMIT_ONE)
    def test_home_returns_429(self):
        first = self.client.post("/", _person(message="Привіт"))
        self.assertEqual(first.status_code, 302)
        blocked = self.client.post("/", _person(message="Привіт"))
        self.assertContains(blocked, TOO_MANY, status_code=429)
        self.assertEqual(Inquiry.objects.count(), 1)

    @override_settings(RATE_LIMITS=LIMIT_ONE)
    def test_contact_and_waitlist_return_429(self):
        self.client.post("/zvorotnyi-zvyazok/", _person(message="Привіт"))
        blocked = self.client.post("/zvorotnyi-zvyazok/", _person(message="Ще"))
        self.assertContains(blocked, TOO_MANY, status_code=429)
        self.client.post(
            "/svyatkovi-boksy/",
            {"email": "guest@example.com", "consent": "on"},
            HTTP_HX_REQUEST="true",
        )
        limited = self.client.post(
            "/svyatkovi-boksy/",
            {"email": "other@example.com", "consent": "on"},
            HTTP_HX_REQUEST="true",
        )
        self.assertContains(limited, TOO_MANY, status_code=429)
        self.assertEqual(limited["HX-Retarget"], "#waitlist-form-slot")
        self.assertEqual(Inquiry.objects.filter(kind=Inquiry.Kind.WAITLIST).count(), 1)

    @override_settings(RATE_LIMITS=LIMIT_ONE)
    def test_buy_now_and_checkout_return_429(self):
        payload = _person(address="Київ", sku="GUARD")
        first = self.client.post("/zamovyty-odrazu/", payload)
        self.assertEqual(first.status_code, 302)
        blocked = self.client.post("/zamovyty-odrazu/", payload)
        self.assertContains(blocked, TOO_MANY, status_code=429)
        self.assertEqual(Order.objects.count(), 1)
        self._cart()
        checkout = _person(
            email="olya@example.com",
            delivery_method=Order.Delivery.BRANCH,
            address="Відділення 12",
            payment_method=Order.Payment.ON_DELIVERY,
        )
        placed = self.client.post("/zamovlennia/", checkout)
        self.assertEqual(placed.status_code, 302)
        self._cart()
        limited = self.client.post("/zamovlennia/", checkout)
        self.assertContains(limited, TOO_MANY, status_code=429)
        self.assertEqual(Order.objects.count(), 2)

    @override_settings(RATE_LIMITS=LIMIT_ONE)
    def test_cart_add_is_not_rate_limited(self):
        first = self.client.post("/koshik/dodaty/", {"sku": "GUARD", "qty": "1"})
        second = self.client.post("/koshik/dodaty/", {"sku": "GUARD", "qty": "1"})
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(self.client.session["cart"]["GUARD"], 2)
