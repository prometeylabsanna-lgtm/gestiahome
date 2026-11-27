import re
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone, translation

from src.catalog.models import Category, Product
from src.commerce.models import Order
from src.commerce.services import create_order, row_from_product
from src.commerce.stock_hold import release_expired_holds
from src.commerce.tests_liqpay import LIQPAY_ON, _callback_post


def _customer(method=Order.Payment.CARD):
    return {
        "name": "Оля",
        "phone": "+380671112233",
        "email": "olya@example.com",
        "delivery_method": Order.Delivery.BRANCH,
        "address": "Відділення 12",
        "payment_method": method,
    }


@LIQPAY_ON
class StockHoldTests(TestCase):
    def setUp(self):
        translation.activate("uk")
        category = Category.objects.create(slug="hold-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="HOLD",
            slug="hold",
            name_uk="Полиця",
            price_uah=Decimal("100"),
            price_eur=Decimal("2"),
            stock_qty=5,
        )

    def _order(self, qty=1, method=Order.Payment.CARD, **extra):
        order = create_order(
            source=Order.Source.CART,
            customer=_customer(method),
            rows=[row_from_product(self.product, qty, "uah")],
            currency="uah",
            language="uk",
            **extra,
        )
        if method == Order.Payment.CARD and not order.payment_ref:
            order.payment_ref = f"{order.number}-abcd1234"
            order.save(update_fields=["payment_ref"])
        return order

    def _fail(self, order):
        return self.client.post(reverse("liqpay_callback"), _callback_post(order, status="failure"))

    def _pay(self, order, **extra):
        return self.client.post(reverse("liqpay_callback"), _callback_post(order, status="success", **extra))

    def test_failure_restores_stock_once(self):
        self.product.stock_qty = 1
        self.product.save()
        order = self._order()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 0)
        self.assertEqual(self.product.stock_status, Product.Stock.OUT)

        first = self._fail(order)
        self.assertEqual(first.status_code, 200)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 1)
        self.assertEqual(self.product.stock_status, Product.Stock.IN_STOCK)
        self.assertEqual(order.payment_status, Order.PayStatus.FAILED)
        self.assertFalse(order.stock_held)
        self.assertTrue(order.stock_released)

        second = self._fail(order)
        self.assertEqual(second.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 1)

    def test_fresh_hold_stays_and_expired_hold_returns_once(self):
        order = self._order()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 4)
        self.assertTrue(order.stock_held)
        self.assertIsNotNone(order.hold_until)

        self.assertEqual(release_expired_holds(), 0)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 4)
        self.assertEqual(order.payment_status, Order.PayStatus.AWAITING)

        order.hold_until = timezone.now() - timedelta(minutes=1)
        order.save(update_fields=["hold_until"])
        out = StringIO()
        call_command("release_expired_holds", stdout=out)
        self.assertIn("Повернуто резервів: 1", out.getvalue())
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 5)
        self.assertEqual(self.product.stock_status, Product.Stock.IN_STOCK)
        self.assertEqual(order.payment_status, Order.PayStatus.FAILED)
        self.assertEqual(order.payment_raw_status, "expired")
        self.assertFalse(order.stock_held)
        self.assertTrue(order.stock_released)
        self.assertIsNone(order.hold_until)

        self.assertEqual(release_expired_holds(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 5)

    def test_cash_and_paid_orders_keep_stock(self):
        cash = self._order(method=Order.Payment.ON_DELIVERY)
        self.assertIsNone(cash.hold_until)
        self.assertTrue(cash.stock_held)
        self.assertEqual(cash.payment_status, Order.PayStatus.UNPAID)
        paid = self._order()
        paid.payment_status = Order.PayStatus.PAID
        paid.hold_until = timezone.now() - timedelta(hours=48)
        paid.save(update_fields=["payment_status", "hold_until"])

        self.assertEqual(release_expired_holds(), 0)
        self.product.refresh_from_db()
        cash.refresh_from_db()
        paid.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 3)
        self.assertEqual(cash.payment_status, Order.PayStatus.UNPAID)
        self.assertTrue(cash.stock_held)
        self.assertEqual(paid.payment_status, Order.PayStatus.PAID)
        self.assertTrue(paid.stock_held)

    def test_retry_reholds_when_stock_remains(self):
        self.product.stock_qty = 1
        self.product.save()
        order = self._order()
        self._fail(order)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 1)
        session = self.client.session
        session["orders_done"] = [order.number]
        session.save()
        old_ref = order.payment_ref

        page = self.client.get(reverse("order_pay", kwargs={"number": order.number}))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "data-liqpay-auto")
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PayStatus.AWAITING)
        self.assertTrue(order.stock_held)
        self.assertFalse(order.stock_released)
        self.assertNotEqual(order.payment_ref, old_ref)
        self.assertEqual(self.product.stock_qty, 0)

    def test_retry_without_stock_does_not_open_liqpay(self):
        self.product.stock_qty = 1
        self.product.save()
        order = self._order()
        self._fail(order)
        self.product.stock_qty = 0
        self.product.stock_status = Product.Stock.OUT
        self.product.save()
        session = self.client.session
        session["orders_done"] = [order.number]
        session.save()
        ref = order.payment_ref

        page = self.client.get(reverse("order_pay", kwargs={"number": order.number}))
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "data-liqpay-auto")
        self.assertContains(page, "вже немає в наявності")
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PayStatus.FAILED)
        self.assertEqual(order.payment_ref, ref)
        self.assertEqual(self.product.stock_qty, 0)
        self.assertFalse(order.stock_short)

    def test_late_paid_reholds_when_stock_exists(self):
        self.product.stock_qty = 1
        self.product.save()
        order = self._order()
        self._fail(order)
        response = self._pay(order, payment_id="txn-late")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PayStatus.PAID)
        self.assertTrue(order.stock_held)
        self.assertFalse(order.stock_short)
        self.assertEqual(self.product.stock_qty, 0)
        self.assertEqual(self.product.stock_status, Product.Stock.OUT)

    def test_late_paid_without_stock_marks_short(self):
        self.product.stock_qty = 1
        self.product.save()
        order = self._order()
        self._fail(order)
        self.product.stock_qty = 0
        self.product.stock_status = Product.Stock.OUT
        self.product.save()
        response = self._pay(order, payment_id="txn-short")
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PayStatus.PAID)
        self.assertTrue(order.stock_short)
        self.assertFalse(order.stock_held)
        self.assertEqual(self.product.stock_qty, 0)

    def test_second_buyer_checks_out_after_hold_expires(self):
        self.product.stock_qty = 1
        self.product.save()
        first = self._order()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_qty, 0)
        Order.objects.filter(pk=first.pk).update(hold_until=timezone.now() - timedelta(minutes=5))

        buyer = Client()
        session = buyer.session
        session["cart"] = {"HOLD": 1}
        session["currency"] = "uah"
        session.save()
        page = buyer.get("/zamovlennia/")
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        sig = re.search(r'name="cart_sig" value="([^"]*)"', html).group(1)
        idem = re.search(r'name="idem" value="([^"]*)"', html).group(1)
        posted = buyer.post(
            "/zamovlennia/",
            {
                "name": "Іра",
                "phone": "+380671112233",
                "email": "ira@example.com",
                "delivery_method": Order.Delivery.BRANCH,
                "address": "Відділення 3",
                "payment_method": Order.Payment.ON_DELIVERY,
                "consent": "on",
                "cart_sig": sig,
                "idem": idem,
            },
        )
        self.assertEqual(posted.status_code, 302)
        first.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(first.payment_status, Order.PayStatus.FAILED)
        self.assertEqual(first.payment_raw_status, "expired")
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(self.product.stock_qty, 0)
        second = Order.objects.exclude(pk=first.pk).get()
        self.assertEqual(second.payment_method, Order.Payment.ON_DELIVERY)
        self.assertTrue(second.stock_held)
        self.assertIsNone(second.hold_until)
