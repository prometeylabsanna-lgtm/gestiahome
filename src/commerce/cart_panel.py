from django.shortcuts import render
from django.utils.translation import gettext as _

from src.catalog.models import Product
from src.commerce.cart import item_count, lines
from src.commerce.selectors import drawer_addon_items, focus_cart_row, page_suggest_addons
from src.core.utils import format_money


def currency_of(request):
    currency = request.session.get("currency", "uah")
    return currency if currency in {"uah", "eur"} else "uah"


def cart_body_context(request, rows, total, notice=""):
    return {
        "rows": rows,
        "total": total,
        "total_label": format_money(total, currency_of(request)),
        "cart_count": item_count(request),
        "cart_notice": notice,
        "suggest": page_suggest_addons(rows),
    }


def panel_context(request, panel_sku, notice=""):
    currency = currency_of(request)
    rows, total = lines(request, currency)
    focus = focus_cart_row(rows, panel_sku)
    if focus is None and panel_sku:
        product = Product.objects.filter(sku=panel_sku, is_active=True).first()
    else:
        product = focus["product"] if focus is not None else None
    cart_skus = {row["sku"] for row in rows}
    addons = drawer_addon_items(product, cart_skus)
    count = item_count(request)
    return {
        "panel_sku": panel_sku or "",
        "focus": focus,
        "rows": rows,
        "total": total,
        "total_label": format_money(total, currency),
        "cart_count": count,
        "count_label": f"({count})" if count else "",
        "addons": addons,
        "cart_notice": notice,
        "has_addons": bool(addons),
        "aria_cart": _("Кошик"),
    }


def render_panel(request, panel_sku, notice=""):
    return render(
        request,
        "partials/nd/_cart_drawer_body.html",
        panel_context(request, panel_sku, notice=notice),
    )
