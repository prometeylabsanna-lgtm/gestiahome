import base64
import hashlib
import os
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.admin import OrderAdmin
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

# Public LiqPay docs example (not a secret).
_DOC_PRIVATE_KEY = "a4825234f4bae72a0be04eafe9e8e2bada209255"
_DOC_DATA = (
    "eyJwdWJsaWNfa2V5IjoiaTAwMDAwMDAwIiwidmVyc2lvbiI6NywiYWN0aW9uIjoicGF5IiwiYW1vdW50IjoiMyI"
    "sImN1cnJlbmN5IjoiVUFIIiwiZGVzY3JpcHRpb24iOiJ0ZXN0Iiwib3JkZXJfaWQiOiIwMDAwMDEifQ=="
)
_DOC_SHA3_SIGNATURE = "0adgJ8F2Ds5HCVkcz4AlmdLMRoIJf7IxsL3QmeFRz/s="

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _sign_sha1(data: str, private_key: str) -> str:
    digest = hashlib.sha1(f"{private_key}{data}{private_key}".encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


def _callback_post(
    order,
    *,
    status="success",
    amount=None,
    currency="UAH",
    payment_id="txn-1",
    order_id=None,
    public_key="test_pub",
    action="pay",
    private_key="test_priv",
    algo="sha3",
):
    ref = order_id or order.payment_ref or f"{order.number}-deadbeef"
    params = {
        "version": 7,
        "public_key": public_key,
        "action": action,
        "amount": str(amount if amount is not None else order.total),
        "currency": currency,
        "order_id": ref,
        "status": status,
        "payment_id": payment_id,
    }
    data = lp.encode_data(params)
    if algo == "sha1":
        signature = _sign_sha1(data, private_key)
    else:
        signature = lp.sign(data, private_key)
    return {"data": data, "signature": signature}


@LIQPAY_ON
class LiqPayAdapterTests(TestCase):
    def test_sign_verify_roundtrip(self):
        data = lp.encode_data({"a": 1, "b": "x"})
        signature = lp.sign(data)
        self.assertTrue(lp.verify(data, signature))

    def test_sign_matches_liqpay_docs_sha3_vector(self):
        self.assertEqual(lp.sign(_DOC_DATA, _DOC_PRIVATE_KEY), _DOC_SHA3_SIGNATURE)

    def test_verify_accepts_legacy_sha1(self):
        data = lp.encode_data({"amount": "10"})
        signature = _sign_sha1(data, "test_priv")
        self.assertTrue(lp.verify(data, signature, "test_priv"))

    def test_verify_rejects_invalid_and_tampered(self):
        data = lp.encode_data({"amount": "10"})
        signature = lp.sign(data)
        self.assertFalse(lp.verify(data, "not-a-sig"))
        self.assertFalse(lp.verify(data + "x", signature))
        self.assertFalse(lp.verify("", signature))

    def test_verify_false_when_private_key_empty(self):
        data = lp.encode_data({"amount": "10"})
        signature = lp.sign(data, "test_priv")
        self.assertFalse(lp.verify(data, signature, private_key=""))
        self.assertFalse(lp.verify(data, signature, private_key="   "))
        empty_sig = lp.sign(data, "")
        self.assertFalse(lp.verify(data, empty_sig, private_key=""))


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
        self.assertEqual(decoded["version"], 7)
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
        self.assertEqual(decoded["version"], 7)
        self.assertEqual(decoded["amount"], "99.50")
        self.assertEqual(decoded["public_key"], "test_pub")
        self.assertNotIn("private", str(decoded).lower())
        self.assertEqual(built["signature"], lp.sign(built["data"], "test_priv"))


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

    def test_wait_compensation_marks_paid(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="wait_compensation", payment_id="txn-wc"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertIsNotNone(self.order.paid_at)
        self.assertEqual(self.order.payment_raw_status, "wait_compensation")
        self.assertEqual(self.order.payment_txn, "txn-wc")

    def test_wait_accept_stays_awaiting(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, status="wait_accept", payment_id="txn-wa"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertIsNone(self.order.paid_at)
        self.assertEqual(self.order.payment_raw_status, "wait_accept")
        self.assertEqual(self.order.payment_txn, "txn-wa")

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
            "version": 7,
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

    def test_callback_sha3_marks_paid(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, algo="sha3", payment_id="txn-sha3"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_callback_legacy_sha1_marks_paid(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, algo="sha1", payment_id="txn-sha1"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    @override_settings(LIQPAY_ALLOW_SHA1_FALLBACK=False)
    def test_callback_sha1_rejected_when_fallback_disabled(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, algo="sha1", payment_id="txn-sha1-off"),
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertEqual(self.order.payment_raw_status, "")
        self.assertEqual(self.order.payment_txn, "")

    @override_settings(LIQPAY_ALLOW_SHA1_FALLBACK=True)
    def test_callback_sha1_accepted_when_fallback_enabled(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, algo="sha1", payment_id="txn-sha1-on"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.order.payment_txn, "txn-sha1-on")

    @override_settings(LIQPAY_ALLOW_SHA1_FALLBACK=False)
    def test_callback_sha3_accepted_when_sha1_fallback_disabled(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, algo="sha3", payment_id="txn-sha3-nofall"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    @override_settings(LIQPAY_ALLOW_SHA1_FALLBACK=True)
    def test_callback_sha3_accepted_when_sha1_fallback_enabled(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, algo="sha3", payment_id="txn-sha3-fall"),
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_callback_wrong_signature_400(self):
        payload = _callback_post(self.order)
        payload["signature"] = lp.sign(payload["data"], "other-key")
        response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

    def test_eur_order_currency_rejected(self):
        self.order.currency = "eur"
        self.order.save(update_fields=["currency"])
        response = self.client.post(reverse("liqpay_callback"), _callback_post(self.order))
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertNotEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_wrong_public_key_rejected(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, public_key="other_pub"),
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

    def test_non_pay_action_rejected(self):
        response = self.client.post(
            reverse("liqpay_callback"),
            _callback_post(self.order, action="hold"),
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

    def test_non_ascii_signature_400(self):
        payload = _callback_post(self.order)
        payload["signature"] = "é"
        response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

    def test_non_ascii_data_400(self):
        payload = _callback_post(self.order)
        payload["data"] = payload["data"] + "ї"
        response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)

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


class LiqPaySecurityFailClosedTests(TestCase):
    def setUp(self):
        cache.clear()
        self.order = Order.objects.create(
            number="GS250101-SEC01",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            payment_ref="GS250101-SEC01-abcd1234",
            total=Decimal("100.00"),
            consent=True,
        )

    def _assert_disabled_callback(self, *, public_key, private_key, algo):
        empty_key = ""
        payload = _callback_post(self.order, private_key=empty_key, algo=algo)
        with override_settings(
            LIQPAY_PUBLIC_KEY=public_key,
            LIQPAY_PRIVATE_KEY=private_key,
            LIQPAY_SANDBOX=False,
        ):
            response = self.client.post(reverse("liqpay_callback"), payload)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content, b"disabled")
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.AWAITING)
        self.assertEqual(self.order.payment_raw_status, "")
        self.assertEqual(self.order.payment_txn, "")

    def test_disabled_empty_private_with_public_sha3(self):
        self._assert_disabled_callback(public_key="test_pub", private_key="", algo="sha3")

    def test_disabled_empty_private_with_public_sha1(self):
        self._assert_disabled_callback(public_key="test_pub", private_key="", algo="sha1")

    def test_disabled_both_keys_empty_sha3(self):
        self._assert_disabled_callback(public_key="", private_key="", algo="sha3")

    def test_disabled_both_keys_empty_sha1(self):
        self._assert_disabled_callback(public_key="", private_key="", algo="sha1")


@LIQPAY_ON
class LiqPaySecurityCheckoutLockTests(TestCase):
    def setUp(self):
        cache.clear()
        self.order = Order.objects.create(
            number="GS250101-SEC07",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.FAILED,
            payment_ref="GS250101-SEC07-oldref00",
            total=Decimal("50.00"),
            consent=True,
        )

    def test_ensure_payment_ref_paid_race_stays_paid(self):
        stale = Order.objects.get(pk=self.order.pk)
        self.assertEqual(stale.payment_status, Order.PayStatus.FAILED)
        Order.objects.filter(pk=self.order.pk).update(
            payment_status=Order.PayStatus.PAID,
            payment_ref="GS250101-SEC07-paidref1",
        )
        ref = lp.ensure_payment_ref(stale)
        self.assertEqual(ref, "GS250101-SEC07-paidref1")
        self.assertEqual(stale.payment_status, Order.PayStatus.PAID)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.order.payment_ref, "GS250101-SEC07-paidref1")

    def test_build_checkout_paid_race_returns_empty_payload(self):
        stale = Order.objects.get(pk=self.order.pk)
        self.assertEqual(stale.payment_status, Order.PayStatus.FAILED)
        Order.objects.filter(pk=self.order.pk).update(payment_status=Order.PayStatus.PAID)
        payload = lp.build_checkout(stale, None)
        self.assertEqual(stale.payment_status, Order.PayStatus.PAID)
        self.assertEqual(payload["data"], "")
        self.assertEqual(payload["signature"], "")

    def test_order_pay_redirects_when_already_paid(self):
        session = self.client.session
        session["orders_done"] = [self.order.number]
        session.save()
        Order.objects.filter(pk=self.order.pk).update(payment_status=Order.PayStatus.PAID)
        response = self.client.get(reverse("order_pay", kwargs={"number": self.order.number}))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("thanks"), response["Location"])
        self.assertIn(self.order.number, response["Location"])
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PayStatus.PAID)

    def test_build_checkout_refuses_eur(self):
        self.order.currency = "eur"
        self.order.payment_status = Order.PayStatus.AWAITING
        self.order.save(update_fields=["currency", "payment_status"])
        with self.assertRaises(ValueError):
            lp.build_checkout(self.order, None)


@LIQPAY_ON
class LiqPayAdminReadonlyTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username="lp-admin",
            email="lp-admin@example.com",
            password="x",
        )
        self.factory = RequestFactory()
        self.admin = OrderAdmin(Order, AdminSite())
        self.card_order = Order.objects.create(
            number="GS250101-ADMIN1",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            total=Decimal("10.00"),
            consent=True,
        )
        self.cash_order = Order.objects.create(
            number="GS250101-ADMIN2",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.ON_DELIVERY,
            payment_status=Order.PayStatus.UNPAID,
            total=Decimal("10.00"),
            consent=True,
        )

    def test_card_order_payment_fields_readonly(self):
        request = self.factory.get("/admin/")
        request.user = self.user
        fields = self.admin.get_readonly_fields(request, self.card_order)
        for name in ("payment_status", "payment_method", "currency", "total"):
            self.assertIn(name, fields)

    def test_non_card_order_payment_fields_editable(self):
        request = self.factory.get("/admin/")
        request.user = self.user
        fields = self.admin.get_readonly_fields(request, self.cash_order)
        self.assertNotIn("payment_status", fields)
        self.assertNotIn("payment_method", fields)
        self.assertNotIn("currency", fields)
        self.assertIn("total", fields)


@LIQPAY_ON
class LiqPayAdminManualConfirmTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.User = User
        self.change_perm = Permission.objects.get(
            content_type__app_label="commerce",
            codename="change_order",
        )
        self.confirm_perm = Permission.objects.get(
            content_type__app_label="commerce",
            codename="confirm_payment_manually",
        )
        self.staff = User.objects.create_user(
            username="lp-staff",
            email="lp-staff@example.com",
            password="x",
            is_staff=True,
        )
        self.staff.user_permissions.add(self.change_perm)
        self.allowed = User.objects.create_user(
            username="lp-confirm",
            email="lp-confirm@example.com",
            password="x",
            is_staff=True,
        )
        self.allowed.user_permissions.add(self.change_perm, self.confirm_perm)
        self.card_order = Order.objects.create(
            number="GS250101-MANUAL1",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            payment_ref="GS250101-MANUAL1-abcd",
            total=Decimal("10.00"),
            consent=True,
        )
        self.cash_order = Order.objects.create(
            number="GS250101-MANUAL2",
            source=Order.Source.CART,
            customer_name="Оля",
            phone="+380671112233",
            email="a@b.c",
            currency="uah",
            delivery_method=Order.Delivery.BRANCH,
            delivery_address="Київ",
            payment_method=Order.Payment.ON_DELIVERY,
            payment_status=Order.PayStatus.UNPAID,
            total=Decimal("10.00"),
            consent=True,
        )
        self.changelist = reverse("admin:commerce_order_changelist")

    def _post_action(self, user, *order_pks):
        client = Client()
        client.force_login(user)
        return client.post(
            self.changelist,
            {
                "action": "confirm_payment_manually",
                "_selected_action": [str(pk) for pk in order_pks],
            },
            follow=True,
        )

    def test_action_hidden_without_permission(self):
        admin = OrderAdmin(Order, AdminSite())
        request = RequestFactory().get("/admin/")
        request.user = self.staff
        actions = admin.get_actions(request)
        self.assertNotIn("confirm_payment_manually", actions)

    def test_action_rejected_without_permission_order_unchanged(self):
        response = self._post_action(self.staff, self.card_order.pk)
        self.assertEqual(response.status_code, 200)
        self.card_order.refresh_from_db()
        self.assertEqual(self.card_order.payment_status, Order.PayStatus.AWAITING)
        self.assertIsNone(self.card_order.paid_at)
        self.assertEqual(self.card_order.payment_raw_status, "")
        self.assertFalse(
            LogEntry.objects.filter(object_id=str(self.card_order.pk)).exists()
        )

    def test_action_with_permission_marks_paid_and_logs(self):
        response = self._post_action(self.allowed, self.card_order.pk)
        self.assertEqual(response.status_code, 200)
        self.card_order.refresh_from_db()
        self.assertEqual(self.card_order.payment_status, Order.PayStatus.PAID)
        self.assertIsNotNone(self.card_order.paid_at)
        self.assertEqual(self.card_order.payment_raw_status, "manual")
        entry = LogEntry.objects.get(object_id=str(self.card_order.pk))
        self.assertEqual(entry.user_id, self.allowed.pk)
        self.assertIn("Оплату підтверджено вручну", entry.get_change_message())

    def test_non_card_order_skipped_no_log(self):
        response = self._post_action(self.allowed, self.cash_order.pk)
        self.assertEqual(response.status_code, 200)
        self.cash_order.refresh_from_db()
        self.assertEqual(self.cash_order.payment_status, Order.PayStatus.UNPAID)
        self.assertIsNone(self.cash_order.paid_at)
        self.assertEqual(self.cash_order.payment_raw_status, "")
        self.assertFalse(
            LogEntry.objects.filter(object_id=str(self.cash_order.pk)).exists()
        )

    def test_already_paid_keeps_paid_at(self):
        from django.utils import timezone as dj_tz

        fixed = dj_tz.now().replace(microsecond=0)
        Order.objects.filter(pk=self.card_order.pk).update(
            payment_status=Order.PayStatus.PAID,
            paid_at=fixed,
            payment_raw_status="success",
        )
        self.card_order.refresh_from_db()
        paid_at = self.card_order.paid_at
        response = self._post_action(self.allowed, self.card_order.pk)
        self.assertEqual(response.status_code, 200)
        self.card_order.refresh_from_db()
        self.assertEqual(self.card_order.payment_status, Order.PayStatus.PAID)
        self.assertEqual(self.card_order.paid_at, paid_at)
        self.assertEqual(self.card_order.payment_raw_status, "success")
        self.assertFalse(
            LogEntry.objects.filter(
                object_id=str(self.card_order.pk),
                change_message__contains="Оплату підтверджено вручну",
            ).exists()
        )


class LiqPayVercelDemoDisabledTests(TestCase):
    def test_vercel_settings_force_liqpay_disabled(self):
        env = {
            "HOME": os.environ.get("HOME", ""),
            "PATH": os.environ.get("PATH", ""),
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
            "DJANGO_SETTINGS_MODULE": "config.settings.vercel",
            "VERCEL": "1",
            "SECRET_KEY": "",
            "ALLOWED_HOSTS": "",
            "CSRF_TRUSTED_ORIGINS": "",
            "SITE_URL": "",
            "DATABASE_URL": "",
            "ADMIN_URL": "",
            "SECURE_SSL_REDIRECT": "False",
            "LIQPAY_PUBLIC_KEY": "dummy_pub",
            "LIQPAY_PRIVATE_KEY": "dummy_priv",
            "LIQPAY_SANDBOX": "1",
        }
        code = (
            "import django\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "from src.commerce.payments.liqpay import enabled\n"
            "print('enabled', enabled())\n"
            "print('public_empty', settings.LIQPAY_PUBLIC_KEY == '')\n"
            "print('private_empty', settings.LIQPAY_PRIVATE_KEY == '')\n"
            "print('sandbox', settings.LIQPAY_SANDBOX)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(_PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("enabled False", result.stdout)
        self.assertIn("public_empty True", result.stdout)
        self.assertIn("private_empty True", result.stdout)
        self.assertIn("sandbox False", result.stdout)


class LiqPayProductionSandboxGuardTests(TestCase):
    def _run_production_import(self, sandbox_value: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env.update(
            {
                "DJANGO_SETTINGS_MODULE": "config.settings.production",
                "SECRET_KEY": "dummy-production-secret-key-for-test",
                "DATABASE_URL": "postgres://u:p@localhost:5432/db",
                "ALLOWED_HOSTS": "example.com",
                "LIQPAY_SANDBOX": sandbox_value,
                "LIQPAY_PUBLIC_KEY": "",
                "LIQPAY_PRIVATE_KEY": "",
                "SECURE_SSL_REDIRECT": "0",
                "SECURE_HSTS_SECONDS": "0",
                "SECURE_HSTS_INCLUDE_SUBDOMAINS": "0",
                "CSRF_TRUSTED_ORIGINS": "",
                "CSP_REPORT_ONLY": "1",
                "TRUST_X_FORWARDED_FOR": "0",
                "SITE_URL": "https://example.com",
                "ADMIN_URL": "admin/",
                "DEFAULT_FROM_EMAIL": "shop@example.com",
                "ORDER_NOTIFY_EMAIL": "",
                "TELEGRAM_BOT_TOKEN": "",
                "TELEGRAM_CHAT_ID": "",
                "NOVA_POSHTA_API_KEY": "",
            }
        )
        code = (
            "import django\n"
            "import config.settings.production\n"
        )
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(_PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_production_rejects_liqpay_sandbox(self):
        result = self._run_production_import("1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("LIQPAY_SANDBOX", result.stderr)

    def test_production_allows_liqpay_sandbox_off(self):
        result = self._run_production_import("0")
        self.assertEqual(result.returncode, 0, msg=result.stderr)


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
