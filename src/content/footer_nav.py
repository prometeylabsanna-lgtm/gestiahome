"""Автопосилання футера: категорії каталогу + юридичні сторінки."""

from types import SimpleNamespace

from django.urls import reverse
from django.utils.translation import gettext as _


def build_footer_columns():
    from src.catalog.models import Category
    from src.content.models_legal import LegalPage

    categories = [
        SimpleNamespace(label=_("Усі товари"), href=reverse("catalog"), underlined=False),
    ]
    for cat in Category.objects.filter(parent__isnull=True, is_active=True).order_by("sort", "name_uk"):
        categories.append(
            SimpleNamespace(label=cat.name, href=cat.get_absolute_url(), underlined=False)
        )

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

    return {
        "category": categories,
        "info": [],
        "legal": legal,
    }
