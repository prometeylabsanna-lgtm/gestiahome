"""LiqPay checkout + server callback adapter.

LiqPay is UAH-only: EUR orders never get card checkout (treated as disabled).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from src.commerce.models import Order

logger = logging.getLogger(__name__)

CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"
_JSON_SEP = (",", ":")


def enabled() -> bool:
    return bool(settings.LIQPAY_PUBLIC_KEY) and bool(settings.LIQPAY_PRIVATE_KEY)


def encode_data(params: dict) -> str:
    raw = json.dumps(params, ensure_ascii=False, separators=_JSON_SEP).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def sign(data: str, private_key: str | None = None) -> str:
    key = private_key if private_key is not None else settings.LIQPAY_PRIVATE_KEY
    digest = hashlib.sha1(f"{key}{data}{key}".encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


def verify(data: str, signature: str, private_key: str | None = None) -> bool:
    if not data or not signature:
        return False
    expected = sign(data, private_key)
    return hmac.compare_digest(expected, signature)


def _absolute(path: str, request) -> str:
    base = str(getattr(settings, "SITE_URL", "") or "").strip().rstrip("/")
    if base:
        return f"{base}{path}"
    if request is not None:
        return request.build_absolute_uri(path)
    return path


def _new_payment_ref(order: Order) -> str:
    return f"{order.number}-{secrets.token_hex(4)}"


def ensure_payment_ref(order: Order) -> str:
    """Reuse payment_ref while awaiting/unpaid; after failed — new suffix + awaiting."""
    if order.payment_status == Order.PayStatus.FAILED:
        order.payment_ref = _new_payment_ref(order)
        order.payment_status = Order.PayStatus.AWAITING
        order.payment_raw_status = ""
        order.save(update_fields=["payment_ref", "payment_status", "payment_raw_status"])
        return order.payment_ref
    if not order.payment_ref:
        order.payment_ref = _new_payment_ref(order)
        order.save(update_fields=["payment_ref"])
    return order.payment_ref


def build_checkout(order: Order, request) -> dict:
    """Return {checkout_url, data, signature} from server-side order totals."""
    payment_ref = ensure_payment_ref(order)
    thanks_path = f"{reverse('thanks')}?kind=order&number={order.number}"
    callback_path = reverse("liqpay_callback")
    params = {
        "version": 3,
        "public_key": settings.LIQPAY_PUBLIC_KEY,
        "action": "pay",
        "amount": str(order.total),
        "currency": "UAH",
        "description": f"Gestia — замовлення №{order.number}",
        "order_id": payment_ref,
        "result_url": _absolute(thanks_path, request),
        "server_url": _absolute(callback_path, request),
    }
    if settings.LIQPAY_SANDBOX:
        params["sandbox"] = "1"
    data = encode_data(params)
    return {
        "checkout_url": CHECKOUT_URL,
        "data": data,
        "signature": sign(data),
        "order": order,
    }


def _decode_payload(data_b64: str) -> dict | None:
    try:
        raw = base64.b64decode(data_b64, validate=True)
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _order_number_from_ref(order_id: str) -> str:
    raw = str(order_id or "").strip()
    if not raw:
        return ""
    return raw.rsplit("-", 1)[0]


def handle_callback(data: str, signature: str) -> tuple[int, str]:
    data = str(data or "")
    signature = str(signature or "")
    if not data or not signature:
        return 400, "bad request"
    if not verify(data, signature):
        return 400, "bad signature"
    payload = _decode_payload(data)
    if payload is None:
        return 400, "bad data"

    order_id = str(payload.get("order_id") or "").strip()
    number = _order_number_from_ref(order_id)
    if not number:
        return 404, "not found"

    status = str(payload.get("status") or "").strip()
    txn = str(payload.get("payment_id") or payload.get("transaction_id") or "").strip()

    try:
        amount = Decimal(str(payload.get("amount")))
    except (InvalidOperation, TypeError, ValueError):
        return 400, "bad amount"
    currency = str(payload.get("currency") or "").strip()

    with transaction.atomic():
        order = (
            Order.objects.select_for_update()
            .filter(number=number)
            .first()
        )
        if order is None:
            return 404, "not found"

        # Record last verified callback order_id + raw status (never keys/signature).
        order.payment_ref = order_id
        order.payment_raw_status = status
        fields = ["payment_ref", "payment_raw_status"]

        if amount != order.total or currency != "UAH":
            logger.warning(
                "liqpay amount/currency mismatch order=%s amount=%s currency=%s",
                order.number,
                payload.get("amount"),
                currency,
            )
            order.save(update_fields=fields)
            return 400, "mismatch"

        # Idempotency: paid stays paid. Failure/reversed after paid must not downgrade.
        if order.payment_status == Order.PayStatus.PAID:
            if status in ("failure", "error", "reversed"):
                logger.warning(
                    "liqpay %s after paid ignored order=%s",
                    status,
                    order.number,
                )
            if txn and not order.payment_txn:
                order.payment_txn = txn[:64]
                fields.append("payment_txn")
            order.save(update_fields=fields)
            return 200, "OK"

        if status == "success" or (status == "sandbox" and settings.LIQPAY_SANDBOX):
            order.payment_status = Order.PayStatus.PAID
            order.paid_at = timezone.now()
            fields.extend(["payment_status", "paid_at"])
            if txn:
                order.payment_txn = txn[:64]
                fields.append("payment_txn")
            order.save(update_fields=fields)
            return 200, "OK"

        if status in ("failure", "error", "reversed"):
            order.payment_status = Order.PayStatus.FAILED
            fields.append("payment_status")
            if txn:
                order.payment_txn = txn[:64]
                fields.append("payment_txn")
            order.save(update_fields=fields)
            return 200, "OK"

        # processing / wait_* / 3ds_verify / etc. — stay awaiting, record raw only
        if txn and not order.payment_txn:
            order.payment_txn = txn[:64]
            fields.append("payment_txn")
        order.save(update_fields=fields)
        return 200, "OK"
