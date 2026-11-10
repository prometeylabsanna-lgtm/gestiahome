"""Card payment providers. Views call only these helpers — no LiqPay branching outside."""

from __future__ import annotations

from src.commerce.payments import liqpay

# LiqPay accepts UAH only; EUR card checkout is disabled (same as keys missing).
_CARD_CURRENCY = "uah"


def card_enabled(currency: str | None = None) -> bool:
    if not liqpay.enabled():
        return False
    if currency is not None and str(currency).lower() != _CARD_CURRENCY:
        return False
    return True


def build_checkout(order, request) -> dict:
    return liqpay.build_checkout(order, request)


def handle_callback(data: str, signature: str) -> tuple[int, str]:
    return liqpay.handle_callback(data, signature)


CHECKOUT_URL = liqpay.CHECKOUT_URL
