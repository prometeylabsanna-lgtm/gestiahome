from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from src.catalog.models import Category, Product
from src.commerce.forms import CallbackForm, CheckoutForm, ContactForm, style_form
from src.commerce.models import Inquiry
from src.commerce.services import create_inquiry

CART_QUOTA = {
    "default": {"limit": 10000, "window": 600},
    "cart": {"limit": 60, "window": 600},
}
NP_QUOTA = {
    "default": {"limit": 10000, "window": 600},
    "np": {"limit": 30, "window": 600},
}


class FieldLimitTests(TestCase):
    def setUp(self):
        category = Category.objects.create(slug="limit-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="LIMITED",
            slug="limited-box",
            name_uk="Бокс",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=5,
        )

    def test_message_over_2000_is_rejected(self):
        form = ContactForm(
            data={
                "name": "Оля",
                "phone": "+380671112233",
                "message": "а" * 2001,
                "consent": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_message_field_renders_maxlength(self):
        form = style_form(ContactForm())
        self.assertEqual(form.fields["message"].widget.attrs["maxlength"], "2000")
        self.assertEqual(form.fields["name"].widget.attrs["maxlength"], "120")

    def test_message_strips_html_and_controls(self):
        form = ContactForm(
            data={
                "name": "Оля",
                "phone": "+380671112233",
                "message": "  Привіт <b>світ</b>\x07<script>alert(1)</script>\n",
                "consent": "on",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["message"], "Привіт світalert(1)")

    def test_email_max_length_is_254(self):
        self.assertEqual(CheckoutForm().fields["email"].max_length, 254)

    def test_callback_sku_over_64_is_rejected(self):
        form = CallbackForm(
            data={
                "name": "Оля",
                "phone": "+380671112233",
                "sku": "A" * 65,
                "consent": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("sku", form.errors)

    def test_unknown_sku_is_not_stored(self):
        inquiry = create_inquiry(
            kind=Inquiry.Kind.CALLBACK,
            name="Оля",
            phone="+380671112233",
            consent=True,
            sku="NO-SUCH",
        )
        self.assertEqual(inquiry.sku, "")
        self.assertIsNone(inquiry.product)

    def test_known_sku_is_stored(self):
        inquiry = create_inquiry(
            kind=Inquiry.Kind.CALLBACK,
            name="Оля",
            phone="+380671112233",
            consent=True,
            sku="LIMITED",
        )
        self.assertEqual(inquiry.sku, "LIMITED")
        self.assertEqual(inquiry.product_id, self.product.pk)


@override_settings(RATE_LIMITS=NP_QUOTA)
class NovaPoshtaLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch("src.commerce.views.novaposhta.search_cities", return_value=[])
    def test_31st_cities_request_is_429(self, search):
        for _ in range(30):
            response = self.client.get("/zamovlennia/np/cities/", {"q": "Київ"})
            self.assertNotEqual(response.status_code, 429)
        blocked = self.client.get("/zamovlennia/np/cities/", {"q": "Київ"})
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(search.call_count, 30)

    @patch("src.commerce.views.novaposhta.search_cities", return_value=[])
    def test_long_city_query_is_400_without_api(self, search):
        response = self.client.get("/zamovlennia/np/cities/", {"q": "а" * 81})
        self.assertEqual(response.status_code, 400)
        search.assert_not_called()

    @patch("src.commerce.views.novaposhta.warehouses_for_city", return_value=[])
    def test_long_city_ref_is_400_without_api(self, warehouses):
        response = self.client.get(
            "/zamovlennia/np/warehouses/",
            {"city_ref": "x" * 65},
        )
        self.assertEqual(response.status_code, 400)
        warehouses.assert_not_called()


@override_settings(RATE_LIMITS=CART_QUOTA)
class CartLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        category = Category.objects.create(slug="cart-limit", name_uk="Каталог")
        Product.objects.create(
            category=category,
            sku="CARTLIM",
            slug="cart-limit-box",
            name_uk="Бокс",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=500,
        )

    def tearDown(self):
        cache.clear()

    def test_61st_cart_add_is_429(self):
        for _ in range(60):
            response = self.client.post("/koshik/dodaty/", {"sku": "CARTLIM", "qty": "1"})
            self.assertNotEqual(response.status_code, 429)
        blocked = self.client.post("/koshik/dodaty/", {"sku": "CARTLIM", "qty": "1"})
        self.assertEqual(blocked.status_code, 429)
