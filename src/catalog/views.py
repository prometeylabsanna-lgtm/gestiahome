from urllib.parse import urlencode

from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404, render

from src.catalog.models import Category
from src.catalog.selectors import (
    CATALOG_PAGE_SIZE,
    base_products,
    category_scope,
    curated_catalog_products,
    filter_catalog,
    filter_categories,
    filter_groups_for_catalog,
    filters_reset_url,
    parse_catalog_filters,
    pdp_related,
    pdp_set_products,
)
from src.commerce.forms import BuyNowForm, CallbackForm, style_form
from src.commerce.wishlist import sku_set
from src.content.form_labels import apply_labels
from src.content.models import ContactForms, HomeBlock, Review


def _filters_active(parsed):
    return bool(parsed["q"] or parsed["in_stock"] or parsed["attrs"] or parsed["categories"])


def _panel_open(parsed):
    return bool(parsed["attrs"] or parsed["categories"])


def _active_filter_count(parsed):
    count = len(parsed["categories"])
    for values in parsed["attrs"].values():
        count += len(values)
    if parsed["in_stock"]:
        count += 1
    return count


def _load_all_url(request):
    query = QueryDict(mutable=True)
    for key in request.GET:
        if key == "all":
            continue
        query.setlist(key, request.GET.getlist(key))
    query["all"] = "1"
    encoded = urlencode(query, doseq=True)
    return f"{request.path}?{encoded}" if encoded else f"{request.path}?all=1"


_CURATED_SORT_KEYS = {
    "price_asc": (lambda p: p.price_uah, False),
    "price_desc": (lambda p: p.price_uah, True),
    "name": (lambda p: p.name_uk, False),
}


def _curated_first(matched, sort):
    """Як у макеті: фільтр/категорія звужує кураторську сітку FILTERS (з її повторами й порядком).

    Товари, що відповідають фільтру, але не стоять у жодній клітинці, додаються в кінці,
    щоб нові позиції не зникали з категорій. Без клітинок — звичайний список.
    """
    curated = curated_catalog_products()
    if not curated:
        return matched
    ids = {product.pk for product in matched}
    picked = [product for product in curated if product.pk in ids]
    if not picked:
        return matched
    if sort in _CURATED_SORT_KEYS:
        key, reverse = _CURATED_SORT_KEYS[sort]
        picked = sorted(picked, key=key, reverse=reverse)
    seen = {product.pk for product in picked}
    return picked + [product for product in matched if product.pk not in seen]


def _catalog_context(request, category=None):
    parsed = parse_catalog_filters(request.GET)
    qs = base_products()
    if category:
        qs = qs.filter(category_id__in=category_scope(category))
    facet_base = qs
    filtered = filter_catalog(qs, parsed)
    active = _filters_active(parsed)
    use_curated = not category and not active
    if use_curated:
        all_products = curated_catalog_products()
    else:
        all_products = _curated_first(list(filtered), parsed.get("sort") or "")
    show_all = request.GET.get("all") == "1"
    total_count = len(all_products)
    has_more = not show_all and total_count > CATALOG_PAGE_SIZE
    products = all_products if show_all else all_products[:CATALOG_PAGE_SIZE]
    block = HomeBlock.objects.filter(key=HomeBlock.Key.CATALOG).first()
    subcategories = []
    if category:
        subcategories = [child for child in category.children.filter(is_active=True) if child.has_public_products]
    else:
        subcategories = [
            cat
            for cat in Category.objects.filter(parent__isnull=True, is_active=True).order_by("sort")
            if cat.has_public_products
        ]
    return {
        "category": category,
        "products": products,
        "parsed": parsed,
        "filter_groups": filter_groups_for_catalog(facet_base),
        "filter_categories": filter_categories(),
        "panel_open": _panel_open(parsed),
        "filters_open": _panel_open(parsed),
        "subcategories": subcategories,
        "filters_reset_url": filters_reset_url(request),
        "filters_active": bool(parsed["in_stock"] or parsed["attrs"] or parsed["categories"]),
        "active_filter_count": _active_filter_count(parsed),
        "crumbs": category.chain() if category else [],
        "has_more": has_more,
        "show_all": show_all,
        "load_all_url": _load_all_url(request),
        "catalog_cta": block.cta if block else "",
        "wishlist_skus": sku_set(request),
        "use_curated": use_curated,
    }


def catalog(request, slug=None):
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
    context = _catalog_context(request, category)
    template = "catalog/_results.html" if request.headers.get("HX-Request") else "catalog/list.html"
    return render(request, template, context)


def product_detail(request, slug):
    product = get_object_or_404(base_products(), slug=slug)
    if not product.is_active:
        raise Http404
    order = {"style": 0, "color": 1}
    attrs = sorted(
        (attr for attr in product.filter_attrs.all() if attr.show_on_pdp),
        key=lambda attr: (order.get(attr.group.slug, 9), attr.sort),
    )
    blocks = {
        block.key: block
        for block in HomeBlock.objects.filter(key__in=["pdp_ship", "pdp_pay", "pdp_set", "pdp_related", "reviews"])
    }
    return render(
        request,
        "catalog/product.html",
        {
            "product": product,
            "attrs": attrs,
            "set_products": pdp_set_products(product),
            "related": pdp_related(product),
            "ship_block": blocks.get("pdp_ship"),
            "pay_block": blocks.get("pdp_pay"),
            "set_block": blocks.get("pdp_set"),
            "related_block": blocks.get("pdp_related"),
            "reviews_block": blocks.get("reviews"),
            "reviews": Review.objects.filter(placement=Review.Placement.HOME),
            "callback_form": apply_labels(
                style_form(CallbackForm(initial={"sku": product.sku})),
                ContactForms.load(),
            ),
            "buy_form": apply_labels(
                style_form(BuyNowForm(initial={"sku": product.sku})),
                ContactForms.load(),
            ),
            "wishlist_skus": sku_set(request),
        },
    )
