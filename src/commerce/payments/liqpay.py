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
from src.commerce.stock_hold import rehold_stock, release_held_stock

logger = logging.getLogger(__name__)

CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"
_JSON_SEP = (",", ":")
_CARD_CURRENCY = "uah"

# LiqPay docs: wait_compensation = successful, credited in daily settlement.
PAID_STATUSES = frozenset({"success", "wait_compensation"})
FAILED_STATUSES = frozenset({"failure", "error", "reversed"})


def enabled() -> bool:
    return bool(settings.LIQPAY_PUBLIC_KEY) and bool(settings.LIQPAY_PRIVATE_KEY)


def encode_data(params: dict) -> str:
    raw = json.dumps(params, ensure_ascii=False, separators=_JSON_SEP).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def _digest_b64(algo, data: str, key: str) -> bytes:
    digest = algo(f"{key}{data}{key}".encode("utf-8")).digest()
    return base64.b64encode(digest)


def sign(data: str, private_key: str | None = None) -> str:
    key = private_key if private_key is not None else settings.LIQPAY_PRIVATE_KEY
    return _digest_b64(hashlib.sha3_256, data, key).decode("ascii")


def _sign_sha1(data: str, key: str) -> str:
    return _digest_b64(hashlib.sha1, data, key).decode("ascii")


def _ascii_or_none(value: str) -> bytes | None:
    try:
        return value.encode("ascii")
    except UnicodeEncodeError:
        return None


def _match_signature(data: str, signature: str, key: str) -> str | None:
    """Return matched algorithm name, or None."""
    sig_b = _ascii_or_none(signature)
    if sig_b is None or _ascii_or_none(data) is None:
        return None
    if hmac.compare_digest(_digest_b64(hashlib.sha3_256, data, key), sig_b):
        return "sha3-256"
    if settings.LIQPAY_ALLOW_SHA1_FALLBACK and hmac.compare_digest(
        _digest_b64(hashlib.sha1, data, key), sig_b
    ):
        return "sha1"
    return None


def verify(data: str, signature: str, private_key: str | None = None) -> bool:
    if not data or not signature:
        return False
    key = private_key if private_key is not None else settings.LIQPAY_PRIVATE_KEY
    if not str(key or "").strip():
        return False
    return _match_signature(data, signature, key) is not None


def _absolute(path: str, request) -> str:
    base = str(getattr(settings, "SITE_URL", "") or "").strip().rstrip("/")
    if base:
        return f"{base}{path}"
    if request is not None:
        return request.build_absolute_uri(path)
    return path


def _new_payment_ref(order: Order) -> str:
    return f"{order.number}-{secrets.token_hex(4)}"


def _sync_payment_fields(order: Order, locked: Order) -> None:
    order.payment_ref = locked.payment_ref
    order.payment_status = locked.payment_status
    order.payment_raw_status = locked.payment_raw_status
    order.payment_txn = locked.payment_txn
    order.paid_at = locked.paid_at


def ensure_payment_ref(order: Order) -> str:
    """Reuse payment_ref while awaiting. After failed, a new suffix and awaiting.

    If the stock hold was already released, reserve the items again first.
    No stock: stay failed and return an empty ref.
    Runs under select_for_update. If paid after lock — leave unchanged.
    """
    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if locked.payment_status == Order.PayStatus.PAID:
            _sync_payment_fields(order, locked)
            return locked.payment_ref or ""
        if locked.payment_status == Order.PayStatus.FAILED:
            if locked.stock_released and not locked.stock_held:
                if not rehold_stock(locked):
                    _sync_payment_fields(order, locked)
                    return ""
                locked.refresh_from_db()
            locked.payment_ref = _new_payment_ref(locked)
            locked.payment_status = Order.PayStatus.AWAITING
            locked.payment_raw_status = ""
            locked.save(update_fields=["payment_ref", "payment_status", "payment_raw_status"])
            _sync_payment_fields(order, locked)
            return locked.payment_ref
        if not locked.payment_ref:
            locked.payment_ref = _new_payment_ref(locked)
            locked.save(update_fields=["payment_ref"])
        _sync_payment_fields(order, locked)
        return locked.payment_ref


def build_checkout(order: Order, request) -> dict:
    """Return {checkout_url, data, signature} from server-side order totals."""
    if str(order.currency or "").lower() != _CARD_CURRENCY:
        raise ValueError("LiqPay supports UAH only")
    payment_ref = ensure_payment_ref(order)
    if order.payment_status == Order.PayStatus.PAID:
        return {
            "checkout_url": CHECKOUT_URL,
            "data": "",
            "signature": "",
            "order": order,
        }
    if order.payment_status == Order.PayStatus.FAILED or not payment_ref:
        return {
            "checkout_url": CHECKOUT_URL,
            "data": "",
            "signature": "",
            "order": order,
            "stock_blocked": order.payment_status == Order.PayStatus.FAILED,
        }
    thanks_path = f"{reverse('thanks')}?kind=order&number={order.number}"
    callback_path = reverse("liqpay_callback")
    params = {
        "version": 7,
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


def _keys_match(left: str, right: str) -> bool:
    a = (left or "").encode("utf-8")
    b = (right or "").encode("utf-8")
    if len(a) != len(b):
        return False
    return hmac.compare_digest(a, b)


def handle_callback(data: str, signature: str) -> tuple[int, str]:
    if not enabled():
        return 503, "disabled"

    data = str(data or "")
    signature = str(signature or "")
    if not data or not signature:
        return 400, "bad request"
    if _ascii_or_none(data) is None or _ascii_or_none(signature) is None:
        return 400, "bad request"

    key = str(settings.LIQPAY_PRIVATE_KEY or "")
    if not key.strip():
        return 503, "disabled"
    matched = _match_signature(data, signature, key)
    if matched is None:
        return 400, "bad signature"
    logger.info("liqpay callback signature matched algorithm=%s", matched)

    payload = _decode_payload(data)
    if payload is None:
        return 400, "bad data"

    if not _keys_match(str(payload.get("public_key") or ""), str(settings.LIQPAY_PUBLIC_KEY or "")):
        return 400, "bad public_key"
    if str(payload.get("action") or "") != "pay":
        return 400, "bad action"

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

        if order.payment_method != Order.Payment.CARD:
            return 400, "not card"

        # Never overwrite payment_ref with callback order_id (may be an older attempt).
        order.payment_raw_status = status
        fields = ["payment_raw_status"]
        current_attempt = order_id == (order.payment_ref or "")

        order_uah = str(order.currency or "").lower() == _CARD_CURRENCY
        if amount != order.total or currency != "UAH" or not order_uah:
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

        # success / wait_compensation / sandbox: any attempt for this order number → paid
        if status in PAID_STATUSES or (status == "sandbox" and settings.LIQPAY_SANDBOX):
            if order.stock_released and not order.stock_held:
                if not rehold_stock(order):
                    order.stock_short = True
                    fields.append("stock_short")
            order.payment_status = Order.PayStatus.PAID
            order.paid_at = timezone.now()
            fields.extend(["payment_status", "paid_at"])
            if txn:
                order.payment_txn = txn[:64]
                fields.append("payment_txn")
            order.save(update_fields=fields)
            return 200, "OK"

        # failure/error/reversed: only current attempt (payment_ref) may mark failed
        if status in FAILED_STATUSES:
            if current_attempt:
                order.payment_status = Order.PayStatus.FAILED
                fields.append("payment_status")
                if txn:
                    order.payment_txn = txn[:64]
                    fields.append("payment_txn")
                release_held_stock(order)
            order.save(update_fields=fields)
            return 200, "OK"

        # processing / wait_accept / 3ds_verify / etc. — stay awaiting, record raw only
        if txn and not order.payment_txn:
            order.payment_txn = txn[:64]
            fields.append("payment_txn")
        order.save(update_fields=fields)
        return 200, "OK"
