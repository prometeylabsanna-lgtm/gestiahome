import os
import unittest
from decimal import Decimal

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.forms import CheckoutForm
from src.commerce.models import Order
from src.commerce.payments import card_enabled
from src.commerce.payments import liqpay as lp


LIQPAY_ON = override_settings(
    LIQPAY_PUBLIC_KEY="test_pub",
    LIQPAY_PRIVATE_KEY="test_priv",
    LIQPAY_SANDBOX=False,
    SITE_URL="https://shop.test",
)


def _callback_post(order, *, status="success", amount=None, currency="UAH", payment_id="txn-1", order_id=None):
    ref = order_id or order.payment_ref or f"{order.number}-deadbeef"
    params = {
        "version": 3,
        "public_key": "test_pub",
        "action": "pay",
        "amount": str(amount if amount is not None else order.total),
        "currency": currency,
        "order_id": ref,
        "status": status,
        "payment_id": payment_id,
    }
    data = lp.encode_data(params)
    signature = lp.sign(data, "test_priv")
    return {"data": data, "signature": signature}


@LIQPAY_ON
class LiqPayAdapterTests(TestCase):
    def test_sign_verify_roundtrip(self):
        data = lp.encode_data({"a": 1, "b": "x"})
        signature = lp.sign(data)
        self.assertTrue(lp.verify(data, signature))

    def test_verify_rejects_invalid_and_tampered(self):
        data = lp.encode_data({"amount": "10"})
        signature = lp.sign(data)
        self.assertFalse(lp.verify(data, "not-a-sig"))
        self.assertFalse(lp.verify(data + "x", signature))
        self.assertFalse(lp.verify("", signature))


@LIQPAY_ON
class LiqPayCheckoutFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        category = Category.objects.create(slug="lp-cat", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="LP-1",
            slug="lp-1",
            name_uk="Бокс тест",
            price_uah=Decimal("250.50"),
            price_eur=Decimal("6"),
            stock_qty=10,
        )

    def _cart(self, currency="uah"):
        session = self.client.session
        session["cart"] = {"LP-1": 2}
        session["currency"] = currency
        session.save()

    def test_card_checkout_redirects_to_pay_page_with_form(self):
        self._cart()
        response = self.client.post(
            reverse("checkout"),
            {
                "name": "Оля",
                "phone": "+380671112233",
                "email": "olya@example.com",
                "delivery_method": Order.Delivery.BRANCH,
                "city": "Київ",
                "branch": "Відділення 1",
                "payment_method": Order.Payment.CARD,
                "consent": "on",
                "amount": "1.00",
                "total": "1.00",
            },
        )
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("501.00"))
        self.assertEqual(order.payment_status, Order.PayStatus.AWAITING)
        self.assertIn(reverse("order_pay", kwargs={"number": order.number}), response["Location"])

        pay = self.client.get(reverse("order_pay", kwargs={"number": order.number}))
        self.assertEqual(pay.status_code, 200)
        html = pay.content.decode()
        self.assertIn(lp.CHECKOUT_URL, html)
        self.assertIn('name="data"', html)
        self.assertIn('name="signature"', html)
        self.assertIn("Перейти до оплати", html)
        self.assertNotIn("test_priv", html)
        self.assertIn("js/nd/liqpay-autosubmit.js", html)

        order.refresh_from_db()
        built = lp.build_checkout(order, None)
        decoded = lp._decode_payload(built["data"])
        self.assertEqual(decoded["amount"], "501.00")
        self.assertEqual(decoded["currency"], "UAH")
        self.assertTrue(decoded["order_id"].startswith(f"{order.number}-"))
        self.assertNotIn("sandbox", decoded)

    def test_build_checkout_amount_from_order_not_client(self):
        order = Order.objects.create(
            number="GS250101-AAAAAA",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            total=Decimal("99.50"),
            consent=True,
        )
        built = lp.build_checkout(order, None)
        decoded = lp._decode_payload(built["data"])
        self.assertEqual(decoded["amount"], "99.50")
        self.assertEqual(decoded["public_key"], "test_pub")
        self.assertNotIn("private", str(decoded).lower())


@LIQPAY_ON
class LiqPayCallbackTests(TestCase):
    def setUp(self):
        cache.clear()
        self.order = Order.objects.create(
            number="GS250101-BBBBBB",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            payment_ref="GS250101-BBBBBB-abcd1234",
            total=Decimal("100.00"),
            consent=True,
        )

    def test_success_marks_paid_and_stores_txn(self):
        response = self.client.post(reverse("liqpay_callback"), _callback_post(self.order))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.order.payment_txn, "txn-1")
        self.assertEqual(self.order.payment_raw_status, "success")
        self.assertIsNotNone(self.order.paid_at)
        paid_at = self.order.paid_at

        response2 = self.client.post(reverse("liqpay_callback"), _callback_post(self.order, payment_id="txn-2"))
        self.assertEqual(response2.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.order.paid_at, paid_at)
        self.assertEqual(self.order.payment_txn, "txn-1")

    def test_failure_marks_failed(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="failure"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.FAILED)
        self.assertEqual(self.order.payment_raw_status, "failure")

    def test_sandbox_status_paid_only_when_sandbox_setting(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="sandbox"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

        with override_settings(LIQPAY_SANDBOX=True):
            response = self.client.post(
                reverse("liqpay_callback"),
                _callback_post(self.order, status="sandbox"),
            )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_processing_leaves_awaiting(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="processing"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertEqual(self.order.payment_raw_status, "processing")

    def test_failure_after_paid_does_not_downgrade(self):
        self.client.post(reverse("liqpay_callback"), _callback_post(self.order))
        self.order.refresh_from_db()
        paid_at = self.order.paid_at
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="failure"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.order.paid_at, paid_at)
        self.assertEqual(self.order.payment_raw_status, "failure")

    def test_amount_mismatch_not_paid(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, amount="1.00"),
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertNotEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_currency_mismatch_not_paid(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, currency="EUR"),
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

    def test_invalid_signature_400_no_change(self):
        payload = _callback_post(self.order)
        payload["signature"] = "bad"
        response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertEqual(self.order.payment_raw_status, "")

    def test_malformed_data_400(self):
        data = "@@@not-base64@@@"
        signature = lp.sign(data, "test_priv")
        response = self.client.post(
            reverse("liqpay_callback"),
            {"data": data, "signature": signature},
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_order_404(self):
        payload = _callback_post(self.order, order_id="GS-MISSING-ffff")
        response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 404)

    def test_stale_failure_records_raw_only(self):
        current = self.order.payment_ref
        stale = f"{self.order.number}-oldref00"
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="failure", order_id=stale, payment_id="txn-stale"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertEqual(self.order.payment_ref, current)
        self.assertEqual(self.order.payment_raw_status, "failure")
        self.assertEqual(self.order.payment_txn, "")

    def test_success_from_older_attempt_marks_paid_keeps_ref(self):
        current = self.order.payment_ref
        older = f"{self.order.number}-oldref00"
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, order_id=older, payment_id="txn-old"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.order.payment_ref, current)
        self.assertEqual(self.order.payment_txn, "txn-old")

    def test_non_card_order_rejected(self):
        self.order.payment_method = Order.Payment.ON_DELIVERY
        self.order.payment_status = Order.PayStatus.UNPAID
        self.order.save(update_fields=["payment_method", "payment_status"])
        response = self.client.post(reverse("liqpay_callback"), _callback_post(self.order))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"not card")
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.UNPAID)
        self.assertEqual(self.order.payment_raw_status, "")
        self.assertEqual(self.order.payment_txn, "")

    def test_float_amount_matches_decimal_total(self):
        self.order.total = Decimal("1200.00")
        self.order.save(update_fields=["total"])
        params = {
            "version": 3,
            "public_key": "test_pub",
            "action": "pay",
            "amount": 1200.0,
            "currency": "UAH",
            "order_id": self.order.payment_ref,
            "status": "success",
            "payment_id": "txn-float",
        }
        data = lp.encode_data(params)
        payload = {"data": data, "signature": lp.sign(data, "test_priv")}
        response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_callback_csrf_exempt_but_signature_required(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse("liqpay_callback")
        before_status = self.order.payment_status
        before_raw = self.order.payment_raw_status
        before_ref = self.order.payment_ref

        missing = client.post(url, {"data": lp.encode_data({"order_id": self.order.payment_ref})})
        self.assertEqual(missing.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, before_status)
        self.assertEqual(self.order.payment_raw_status, before_raw)
        self.assertEqual(self.order.payment_ref, before_ref)

        forged = _callback_post(self.order)
        forged["signature"] = "forged-signature"
        forged_resp = client.post(url, forged)
        self.assertEqual(forged_resp.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, before_status)
        self.assertEqual(self.order.payment_raw_status, before_raw)
        self.assertEqual(self.order.payment_ref, before_ref)

        ok = client.post(url, _callback_post(self.order))
        self.assertEqual(ok.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_callback_rejects_get(self):
        response = self.client.get(reverse("liqpay_callback"))
        self.assertEqual(response.status_code, 405)


class LiqPayDisabledAndCurrencyTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        category = Category.objects.create(slug="lp-off", name_uk="Каталог")
        self.product = Product.objects.create(
            category=category,
            sku="LP-OFF",
            slug="lp-off",
            name_uk="Бокс",
            price_uah=Decimal("100"),
            price_eur=Decimal("3"),
            stock_qty=5,
        )

    def _cart(self, currency="uah"):
        session = self.client.session
        session["cart"] = {"LP-OFF": 1}
        session["currency"] = currency
        session.save()

    @override_settings(LIQPAY_PUBLIC_KEY="", LIQPAY_PRIVATE_KEY="")
    def test_disabled_hides_card_and_rejects_post(self):
        self.assertFalse(card_enabled("uah"))
        self._cart()
        page = self.client.get(reverse("checkout"))
        html = page.content.decode()
        self.assertNotIn('name="payment_method" value="card"', html)
        self.assertIn('name="payment_method" value="on_delivery"', html)
        form = CheckoutForm(card_enabled=False)
        self.assertEqual(form.fields["payment_method"].initial, Order.Payment.ON_DELIVERY)

        response = self.client.post(
            reverse("checkout"),
            {
                "name": "Оля",
                "phone": "+380671112233",
                "email": "olya@example.com",
                "delivery_method": Order.Delivery.BRANCH,
                "city": "Київ",
                "branch": "1",
                "payment_method": Order.Payment.CARD,
                "consent": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    @LIQPAY_ON
    def test_initial_card_when_enabled(self):
        form = CheckoutForm(card_enabled=True)
        self.assertEqual(form.fields["payment_method"].initial, Order.Payment.CARD)
        self.assertTrue(any(value == Order.Payment.CARD for value, _ in form.fields["payment_method"].choices))

    @LIQPAY_ON
    def test_eur_hides_card(self):
        self.assertFalse(card_enabled("eur"))
        self._cart("eur")
        page = self.client.get(reverse("checkout"))
        html = page.content.decode()
        self.assertNotIn('name="payment_method" value="card"', html)


@LIQPAY_ON
class LiqPayThanksAndCspTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.order = Order.objects.create(
            number="GS250101-CCCCCC",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            total=Decimal("50.00"),
            consent=True,
        )

    def _session(self):
        session = self.client.session
        session["orders_done"] = [self.order.number]
        session.save()

    def test_thanks_awaiting_paid_failed_texts_without_status_change(self):
        self._session()
        url = f"{reverse('thanks')}?kind=order&number={self.order.number}"

        response = self.client.get(url)
        self.assertContains(response, "Очікуємо підтвердження оплати")
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

        self.order.payment_status = Order.PayStatus.PAID
        self.order.save(update_fields=["payment_status"])
        response = self.client.get(url)
        self.assertContains(response, "Оплату отримано")
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

        self.order.payment_status = Order.PayStatus.FAILED
        self.order.save(update_fields=["payment_status"])
        response = self.client.get(url)
        self.assertContains(response, "Оплата не пройшла")
        self.assertContains(response, reverse("order_pay", kwargs={"number": self.order.number}))
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.FAILED)

    def test_csp_form_action_includes_liqpay(self):
        from django.conf import settings

        self.assertIn("https://www.liqpay.ua", settings.CSP_POLICY)
        self.assertIn("form-action 'self'", settings.CSP_POLICY)

    def test_failed_retry_generates_new_payment_ref(self):
        self._session()
        self.order.payment_status = Order.PayStatus.FAILED
        self.order.payment_ref = f"{self.order.number}-oldref00"
        self.order.save(update_fields=["payment_status", "payment_ref"])
        old = self.order.payment_ref
        response = self.client.get(reverse("order_pay", kwargs={"number": self.order.number}))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertNotEqual(self.order.payment_ref, old)
        self.assertTrue(self.order.payment_ref.startswith(f"{self.order.number}-"))

    def _assert_never_cache(self, response):
        cache_control = response.get("Cache-Control", "")
        self.assertTrue(
            "no-store" in cache_control
            or "no-cache" in cache_control
            or "private" in cache_control
            or "max-age=0" in cache_control,
            cache_control,
        )

    def test_order_pay_and_thanks_never_cache(self):
        self._session()
        self.order.payment_ref = f"{self.order.number}-abcd1234"
        self.order.payment_status = Order.PayStatus.AWAITING
        self.order.save(update_fields=["payment_ref", "payment_status"])
        pay = self.client.get(reverse("order_pay", kwargs={"number": self.order.number}))
        self.assertEqual(pay.status_code, 200)
        self._assert_never_cache(pay)
        thanks = self.client.get(f"{reverse('thanks')}?kind=order&number={self.order.number}")
        self.assertEqual(thanks.status_code, 200)
        self._assert_never_cache(thanks)

    def test_thanks_post_without_csrf_redirects_303(self):
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session["orders_done"] = [self.order.number]
        session.save()
        url = f"{reverse('thanks')}?kind=order&number={self.order.number}"
        before = self.order.payment_status
        response = client.post(url, {"status": "success", "order_id": "forged"})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, before)


@unittest.skipUnless(
    bool(os.environ.get("LIQPAY_PUBLIC_KEY")) and bool(os.environ.get("LIQPAY_PRIVATE_KEY")),
    "LIQPAY keys not in process environ",
)
class LiqPayOptionalSandboxBuildTests(TestCase):
    def test_builds_params_locally_without_network(self):
        pub = os.environ["LIQPAY_PUBLIC_KEY"]
        priv = os.environ["LIQPAY_PRIVATE_KEY"]
        order = Order.objects.create(
            number="GS250101-SANDBX",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            total=Decimal("1.00"),
            consent=True,
        )
        with override_settings(
            LIQPAY_PUBLIC_KEY=pub,
            LIQPAY_PRIVATE_KEY=priv,
            LIQPAY_SANDBOX=True,
            SITE_URL="https://shop.test",
        ):
            built = lp.build_checkout(order, None)
        decoded = lp._decode_payload(built["data"])
        self.assertEqual(decoded["sandbox"], "1")
        self.assertEqual(decoded["amount"], "1.00")
        self.assertTrue(lp.verify(built["data"], built["signature"], priv))
