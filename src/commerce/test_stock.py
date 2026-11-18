import re
from decimal import Decimal

from django.contrib import admin
from django.forms.models import modelform_factory
from django.test import Client, TestCase
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.models import Inquiry, Order
from src.commerce.services import (
    OrderValidationError,
    create_order,
    insufficient_stock_message,
    row_from_product,
)


def _customer():
    return {
        "name": "Оля",
        "phone": "+380671112233",
        "email": "olya@example.com",
        "delivery_method": Order.Delivery.BRANCH,
        "address": "Відділення 12",
        "payment_method": Order.Payment.ON_DELIVERY,
    }


def _checkout_payload(**extra):
    data = _customer()
    data["consent"] = "on"
    data.update(extra)
    return data


def _checkout_sig(client):
    html = client.get("/zamovlennia/").content.decode()
    match = re.search(r'name="cart_sig" value="([^"]*)"', html)
    if match is None:
        raise AssertionError("cart_sig missing")
    return match.group(1)


class StockTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        category = Category.objects.create(slug="stock-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="SNIH",
            slug="snih",
            name_uk="Сніг",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=100,
        )

    def _order(self, qty, **extra):
        payload = {
            "source": Order.Source.CART,
            "customer": _customer(),
            "rows": [row_from_product(self.product, qty, "uah")],
            "currency": "uah",
            "language": "uk",
        }
        payload.update(extra)
        return create_order(**payload)

    def test_save_syncs_status_with_quantity(self):
        self.product.stock_qty = 0
        self.product.stock_status = Product.Stock.IN_STOCK
        self.product.save(update_fields=["stock_qty"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_status, Product.Stock.OUT)

        self.product.stock_qty = 4
        self.product.stock_status = Product.Stock.OUT
        self.product.save()
        self.assertEqual(self.product.stock_status, Product.Stock.IN_STOCK)

        self.product.stock_qty = 0
        self.product.stock_status = Product.Stock.ON_ORDER
        self.product.save()
        self.assertEqual(self.product.stock_status, Product.Stock.ON_ORDER)

        self.product.stock_qty = 3
        self.product.stock_status = Product.Stock.ON_ORDER
        self.product.save()
        self.assertEqual(self.product.stock_status, Product.Stock.ON_ORDER)

    def test_insufficient_qty_is_rejected(self):
        self.product.stock_qty = 2
        self.product.save()
        with self.assertRaises(OrderValidationError) as caught:
            self._order(5)
        self.assertEqual(str(caught.exception), "Товару «Сніг» залишилось лише 2 шт.")
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 2)
        self.assertEqual(self.product.stock_status, Product.Stock.IN_STOCK)

    def test_decrement_leaves_remainder_in_stock(self):
        self.product.stock_qty = 7
        self.product.save()
        self._order(3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 4)
        self.assertEqual(self.product.stock_status, Product.Stock.IN_STOCK)
        self.assertEqual(Order.objects.get().items.get().qty, 3)

    def test_repeat_idempotency_key_does_not_decrement_twice(self):
        self.product.stock_qty = 5
        self.product.save()
        first = self._order(2, idempotency_key="same-stock")
        second = self._order(2, idempotency_key="same-stock")
        self.assertEqual(first.pk, second.pk)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 3)

    def test_reaching_zero_sets_out_and_keeps_waitlist(self):
        self.product.stock_qty = 2
        self.product.save()
        self._order(2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 0)
        self.assertEqual(self.product.stock_status, Product.Stock.OUT)
        denied = self.client.post("/koshik/dodaty/", {"sku": "SNIH", "qty": "1"})
        self.assertEqual(denied.status_code, 422)
        buy = self.client.post(
            "/zamovyty-odrazu/",
            {
                "name": "Оля",
                "phone": "+380671112233",
                "address": "Київ",
                "sku": "SNIH",
                "consent": "on",
            },
        )
        self.assertContains(buy, "Цей товар зараз не можна замовити.")
        self.assertEqual(Order.objects.count(), 1)
        wait = self.client.post(
            "/svyatkovi-boksy/",
            {"email": "guest@example.com", "consent": "on"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(wait.status_code, 200)
        self.assertEqual(Inquiry.objects.filter(kind=Inquiry.Kind.WAITLIST).count(), 1)

    def test_on_order_stays_until_quantity_hits_zero(self):
        self.product.stock_status = Product.Stock.ON_ORDER
        self.product.stock_qty = 3
        self.product.save()
        self.assertEqual(self.product.stock_status, Product.Stock.ON_ORDER)
        self._order(1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 2)
        self.assertEqual(self.product.stock_status, Product.Stock.ON_ORDER)
        self._order(2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 0)
        self.assertEqual(self.product.stock_status, Product.Stock.OUT)

    def test_cart_clamps_to_stock_and_rejects_empty(self):
        self.product.stock_qty = 2
        self.product.save()
        added = self.client.post("/koshik/dodaty/", {"sku": "SNIH", "qty": "9"})
        self.assertEqual(added.status_code, 302)
        self.assertEqual(self.client.session["cart"]["SNIH"], 2)
        updated = self.client.post("/koshik/kilkist/", {"sku": "SNIH", "qty": "8"})
        self.assertEqual(updated.status_code, 302)
        self.assertEqual(self.client.session["cart"]["SNIH"], 2)
        self.product.stock_qty = 0
        self.product.save()
        blocked = self.client.post("/koshik/dodaty/", {"sku": "SNIH", "qty": "1"})
        self.assertEqual(blocked.status_code, 422)
        still = self.client.post("/koshik/kilkist/", {"sku": "SNIH", "qty": "1"})
        self.assertEqual(still.status_code, 422)
        cleared = self.client.post("/koshik/kilkist/", {"sku": "SNIH", "qty": "0"})
        self.assertEqual(cleared.status_code, 302)
        self.assertNotIn("SNIH", self.client.session.get("cart", {}))

    def test_cart_and_checkout_mark_rows_over_stock(self):
        self.product.stock_qty = 2
        self.product.save()
        session = self.client.session
        session["cart"] = {"SNIH": 5}
        session.save()
        message = "Товару «Сніг» залишилось лише 2 шт."
        cart = self.client.get("/koshik/")
        self.assertContains(cart, message)
        self.assertContains(cart, 'class="co-error"')
        self.assertContains(cart, "data-over-stock")
        self.assertContains(cart, 'max="2"')
        self.assertEqual(self.client.session["cart"]["SNIH"], 5)
        checkout = self.client.get("/zamovlennia/")
        self.assertContains(checkout, message)
        self.assertContains(checkout, "× 2")
        self.assertNotContains(checkout, "data-over-stock")
        self.assertEqual(self.client.session["cart"]["SNIH"], 2)
        posted = self.client.post("/zamovlennia/", _checkout_payload(cart_sig="0" * 64))
        self.assertEqual(posted.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(self.client.session["cart"]["SNIH"], 2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 2)

    def test_pdp_qty_max_follows_stock(self):
        self.product.stock_qty = 4
        self.product.save()
        page = self.client.get("/tovar/snih/")
        self.assertContains(page, 'name="qty"')
        self.assertContains(page, 'max="4"')

    def test_english_stock_message(self):
        with translation.override("en"):
            self.assertEqual(
                insufficient_stock_message("Snow", 2),
                "Only 2 pcs of “Snow” left.",
            )

    def test_admin_shows_stock_qty(self):
        product_admin = admin.site._registry[Product]
        self.assertIn("stock_qty", product_admin.list_display)
        self.assertIn("stock_qty", product_admin.list_editable)
        self.assertIsNone(product_admin.fields)
        self.assertIsNone(product_admin.exclude)
        declared = [name for _title, options in product_admin.fieldsets for name in options["fields"]]
        self.assertIn("stock_qty", declared)
        form = modelform_factory(Product, fields="__all__")()
        self.assertIn("stock_qty", form.base_fields)

    def test_second_session_cannot_buy_the_last_unit(self):
        self.product.stock_qty = 1
        self.product.save()
        first = Client()
        second = Client()
        signatures = {}
        for client in (first, second):
            session = client.session
            session["cart"] = {"SNIH": 1}
            session["currency"] = "uah"
            session.save()
            signatures[id(client)] = _checkout_sig(client)
        placed = first.post("/zamovlennia/", _checkout_payload(cart_sig=signatures[id(first)]))
        self.assertEqual(placed.status_code, 302)
        rejected = second.post("/zamovlennia/", _checkout_payload(cart_sig=signatures[id(second)]))
        self.assertEqual(rejected.status_code, 302)
        self.assertEqual(rejected["Location"], "/koshik/")
        cart = second.get("/koshik/")
        self.assertContains(cart, "Товар «Сніг» зараз відсутній. Приберіть його з кошика.")
        self.assertNotIn("SNIH", second.session.get("cart", {}))
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 0)
        self.assertEqual(self.product.stock_status, Product.Stock.OUT)
