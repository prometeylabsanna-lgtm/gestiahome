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


def currency_labels() -> tuple[str, str, str]:
    uah, uah_sign, eur = "UAH", "₴", "€"
    try:
        from django.db.utils import OperationalError, ProgrammingError
        from src.content.models import SiteSettings

        site = SiteSettings.load()
        uah = (site.currency_uah or "").strip() or uah
        uah_sign = (site.currency_uah_sign or "").strip() or uah_sign
        eur = (site.currency_eur or "").strip() or eur
    except (OperationalError, ProgrammingError):
        pass
    return uah, uah_sign, eur


def format_money(amount: Decimal, currency: str) -> str:
    quantized = Decimal(amount).quantize(Decimal("0.01"))
    text = f"{quantized:,.2f}".replace(",", " ")
    if text.endswith(".00"):
        text = text[:-3]
    _, uah_sign, eur = currency_labels()
    if currency == "eur":
        return f"{text} {eur}"
    return f"{text} {uah_sign}"
