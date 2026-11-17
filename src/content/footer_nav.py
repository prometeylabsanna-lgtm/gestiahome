"""Автопосилання футера: категорії каталогу + інфо FooterLink + юридичні сторінки.

У макеті колонка категорій: «Усі товари» + 3 перші кореневі категорії.
Колонка info — з FooterLink (CMS).
Колонка legal — FooterLink column=legal (якщо є), інакше LegalPage.
"""

from types import SimpleNamespace

from django.urls import reverse
from django.utils.translation import gettext as _

FOOTER_CATEGORY_LIMIT = 3


def _footer_link_items(column):
    from src.content.models import FooterLink

    items = []
    for link in FooterLink.objects.filter(column=column).order_by("sort", "id"):
        items.append(
            SimpleNamespace(
                label=link.label,
                href=link.href(),
                underlined=bool(link.underlined),
            )
        )
    return items


def _legal_from_pages():
    from src.content.models_legal import LegalPage

    legal = []
    url_by_key = {
        LegalPage.Key.OFFER: "offer",
        LegalPage.Key.PRIVACY: "privacy",
        LegalPage.Key.COOKIES: "cookies",
        LegalPage.Key.SHIPPING: "shipping",
    }
    for page in LegalPage.objects.order_by("key"):
        name = url_by_key.get(page.key)
        if not name:
            continue
        legal.append(
            SimpleNamespace(label=page.title, href=reverse(name), underlined=False)
        )
    return legal


def build_footer_columns():
    from src.catalog.models import Category

    categories = [
        SimpleNamespace(label=_("Усі товари"), href=reverse("catalog"), underlined=False),
    ]
    qs = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .order_by("sort", "name_uk")[:FOOTER_CATEGORY_LIMIT]
    )
    for cat in qs:
        categories.append(
            SimpleNamespace(
                label=cat.name,
                href=cat.get_absolute_url(),
                underlined=bool(cat.menu_featured),
            )
        )

    legal_links = _footer_link_items("legal")
    legal = legal_links if legal_links else _legal_from_pages()

    return {
        "category": categories,
        "info": _footer_link_items("info"),
        "legal": legal,
    }
