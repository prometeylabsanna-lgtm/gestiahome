"""Публічний /llms.txt лише з текстів сайту. Без службового префікса адмінки."""

from __future__ import annotations

from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils.translation import gettext, override

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
        _pair(request, "Головна", "home"),
        _pair(request, "Каталог", "catalog"),
        "",
        "## Категорії",
        "",
    ]
    categories = _category_lines(request)
    lines.extend(categories or ["- Немає активних категорій."])
    collections = _collection_lines(request)
    if collections:
        lines.extend(["", "## Колекції", "", *collections])
    lines.extend(
        [
            "",
            "## Ключові сторінки",
            "",
            _pair(request, "Доставка та оплата", "shipping"),
            _pair(request, "Про нас", "about"),
            _pair(request, "Контакти", "contacts"),
            _pair(request, "Актуальні питання", "faq"),
            _pair(request, "Оферта", "offer"),
            _pair(request, "Конфіденційність", "privacy"),
            _pair(request, "Cookies", "cookies"),
            _contact_lines(request),
            "",
            "## Правила для ШІ",
            "",
            "- Посилайтеся на конкретну сторінку Gestia, з якої взято факт.",
            "- Ціни, наявність і умови змінюються. Перед відповіддю перевіряйте їх на сайті.",
            "- Не використовуйте кошик, оформлення замовлення, подяку, обране, заявку",
            "  та адреси /koshik/, /zamovlennia/, /thank-you/, /diakuiemo/, /obrane/,",
            "  /zayavka/, /zamovyty-odrazu/ (і ті самі шляхи з префіксом /en/) як джерело вмісту.",
            f"- Каталог і картки товарів: {base}/katalog/ та {base}/en/katalog/.",
            "",
        ]
    )
    return "\n".join(lines)


def _md_label(value: str) -> str:
    text = " ".join((value or "").replace("[", "(").replace("]", ")").split())
    return text or BRAND


def _abs(request, viewname: str, *, lang: str, kwargs=None, suffix: str = "") -> str:
    with override(lang):
        path = reverse(viewname, kwargs=kwargs) + suffix
    return public_base(request) + path


def _pair(request, msgid: str, viewname: str) -> str:
    rows = []
    for code, _label in settings.LANGUAGES:
        with override(code):
            label = _md_label(gettext(msgid))
        rows.append(f"- [{label}]({_abs(request, viewname, lang=code)})")
    return "\n".join(rows)


def _contact_lines(request) -> str:
    from src.content.literals import LITERALS

    rows = []
    for code, _label in settings.LANGUAGES:
        label = _md_label(LITERALS["callback_title"][0 if code == "uk" else 1])
        href = _abs(request, "home", lang=code, suffix="#callback")
        rows.append(f"- [{label}]({href})")
    contacts = public_contacts()
    if contacts["phone"]:
        rows.append(f"- Телефон: {contacts['phone']}")
    if contacts["email"]:
        rows.append(f"- Email: {contacts['email']}")
    for address in contacts["addresses"]:
        rows.append(f"- Адреса: {address}")
    for url in contacts["same_as"]:
        rows.append(f"- {url}")
    return "\n".join(rows)


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
    if not text:
        from src.content.literals import LITERALS

        text = " ".join(LITERALS["hero_text"][0].split())
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


def _category_lines(request) -> list[str]:
    from src.catalog.models import Category

    lines = []
    rows = Category.objects.filter(is_active=True).order_by("sort", "name_uk")
    for category in rows:
        for code, _label in settings.LANGUAGES:
            with override(code):
                label = _md_label(category.name)
                href = public_base(request) + category.get_absolute_url()
            lines.append(f"- [{label}]({href})")
    return lines
