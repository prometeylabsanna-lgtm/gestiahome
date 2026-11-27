"""Публічний /llms.txt лише з текстів сайту. Без службового префікса адмінки."""

from __future__ import annotations

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils.translation import override

from src.core.seo import BRAND, clip_text, public_base, public_contacts


def llms_text(request) -> str:
    base = public_base(request)
    lines = [
        "# Gestia",
        "",
        _shop_blurb(),
        "",
        "## Розділи",
        "",
        _pair(request, lambda: _ui_label("crumb_home"), "home"),
        _pair(request, lambda: _ui_label("catalog"), "catalog"),
        "",
        "## Категорії",
        "",
    ]
    categories = _category_lines(request)
    lines.extend(categories or ["- Немає активних категорій."])
    collections = _collection_lines(request)
    if collections:
        lines.extend(["", "## Колекції", "", *collections])
    products = _product_lines(request)
    if products:
        lines.extend(["", "## Товари", "", *products])
    lines.extend(
        [
            "",
            "## Ключові сторінки",
            "",
            _pair(request, lambda: _ui_label("legal_shipping"), "shipping"),
            _pair(request, lambda: _nav_label("nav_about"), "about"),
            _pair(request, lambda: _nav_label("nav_contacts"), "contacts"),
            _pair(request, lambda: _nav_label("nav_faq"), "faq"),
            _pair(request, lambda: _ui_label("legal_offer"), "offer"),
            _pair(request, lambda: _ui_label("legal_privacy"), "privacy"),
            _pair(request, lambda: _ui_label("legal_cookies"), "cookies"),
        ]
    )
    facts = _contact_facts()
    if facts:
        lines.extend(["", facts])
    lines.extend(["", "## Правила для ШІ", "", *_ai_rules(base), ""])
    return "\n".join(lines)


def _md_label(value: str) -> str:
    text = " ".join((value or "").replace("[", "(").replace("]", ")").split())
    return text or BRAND()


def _abs(request, viewname: str, *, lang: str, kwargs=None, suffix: str = "") -> str:
    with override(lang):
        path = reverse(viewname, kwargs=kwargs) + suffix
    return public_base(request) + path


def _pair(request, loader, viewname: str) -> str:
    rows = []
    for code, _label in settings.LANGUAGES:
        with override(code):
            label = _md_label(loader())
        rows.append(f"- [{label}]({_abs(request, viewname, lang=code)})")
    return "\n".join(rows)


def _ui_label(key):
    from src.content.ui_text import text

    return text(key)


def _nav_label(field):
    from src.content.models import SiteSettings
    from src.core.utils import localized

    return localized(SiteSettings.load(), field)


def _enabled_codes() -> list[str]:
    from src.core.middleware import language_enabled

    codes = [settings.LANGUAGE_CODE]
    for code, _label in settings.LANGUAGES:
        if code == settings.LANGUAGE_CODE or not language_enabled(code):
            continue
        codes.append(code)
    return codes


def _contact_facts() -> str:
    contacts = public_contacts()
    rows = []
    if contacts["phone"]:
        rows.append(f"- Телефон: {contacts['phone']}")
    if contacts["email"]:
        rows.append(f"- Email: {contacts['email']}")
    for address in contacts["addresses"]:
        rows.append(f"- Адреса: {address}")
    for url in contacts["same_as"]:
        rows.append(f"- {url}")
    return "\n".join(rows)


def _ai_rules(base: str) -> list[str]:
    from src.core.seo import PRIVATE_PREFIXES

    lines = [
        "- Посилайтеся на конкретну сторінку Gestia, з якої взято факт.",
        "- Ціни, наявність і умови змінюються. Перед відповіддю перевіряйте їх на сайті.",
        "- Не використовуйте кошик, оформлення замовлення, подяку, обране, заявку та службові шляхи як джерело вмісту:",
    ]
    for code in _enabled_codes():
        prefix = "" if code == settings.LANGUAGE_CODE else f"/{code}"
        lines.append("  " + ", ".join(f"{prefix}{path}" for path in PRIVATE_PREFIXES) + ".")
    catalogs = []
    for code in _enabled_codes():
        if code == settings.LANGUAGE_CODE:
            catalogs.append(f"{base}/katalog/")
        else:
            catalogs.append(f"{base}/{code}/katalog/")
    lines.append("- Каталог і картки товарів: " + ", ".join(catalogs) + ".")
    return lines


def _shop_blurb() -> str:
    text = ""
    try:
        from src.content.models import AboutPage, HomeBlock

        hero = HomeBlock.objects.filter(key=HomeBlock.Key.HERO).only("text_uk").first()
        if hero is not None:
            text = " ".join((hero.text_uk or "").split())
        if not text:
            about = AboutPage.load()
            text = " ".join((about.lead_uk or "").split())
            if not text:
                text = " ".join((about.body_uk or "").split())
    except (OperationalError, ProgrammingError, AttributeError):
        text = ""
    return clip_text(text, 500)


def _collection_lines(request) -> list[str]:
    from src.content.models import HomeCollection

    lines = []
    rows = (
        HomeCollection.objects.filter(is_active=True)
        .exclude(slug="")
        .exclude(slug__isnull=True)
        .order_by("sort", "id")
    )
    for collection in rows:
        for code, _label in settings.LANGUAGES:
            with override(code):
                label = _md_label(collection.title)
                href = public_base(request) + collection.get_absolute_url()
            lines.append(f"- [{label}]({href})")
    return lines


def _product_lines(request) -> list[str]:
    from src.catalog.storefront import indexable_products

    lines = []
    rows = indexable_products().order_by("sort", "name_uk", "id")
    for product in rows:
        for code, _label in settings.LANGUAGES:
            with override(code):
                label = _md_label(product.name)
                href = public_base(request) + product.get_absolute_url()
            lines.append(f"- [{label}]({href})")
    return lines


def _category_lines(request) -> list[str]:
    from src.catalog.storefront import indexable_categories

    lines = []
    rows = indexable_categories()
    for category in rows:
        for code, _label in settings.LANGUAGES:
            with override(code):
                label = _md_label(category.name)
                href = public_base(request) + category.get_absolute_url()
            lines.append(f"- [{label}]({href})")
    return lines
