from decimal import Decimal

from django.utils.translation import get_language

SUPPORTED = ("uk", "en", "fr")


def curly_to_guillemets(value: str) -> str:
    if not isinstance(value, str) or ("“" not in value and "”" not in value):
        return value
    return value.replace("“", "«").replace("”", "»")


def localized(obj, field: str, language: str | None = None) -> str:
    lang = (language or get_language() or "uk").split("-")[0]
    if lang not in SUPPORTED:
        lang = "uk"
    value = getattr(obj, f"{field}_{lang}", "") or ""
    if not value and lang != "uk":
        value = getattr(obj, f"{field}_uk", "") or ""
    return value


def format_money(amount: Decimal, currency: str) -> str:
    quantized = Decimal(amount).quantize(Decimal("0.01"))
    text = f"{quantized:,.2f}".replace(",", " ")
    if text.endswith(".00"):
        text = text[:-3]
    if currency == "eur":
        return f"{text} €"
    return f"{text} ₴"
