from decimal import Decimal
from urllib.parse import urlencode

from django.http import Http404, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render

from src.catalog.menu_filters import accessory_crumb, menu_facets
from src.catalog.models import Category
from src.catalog.selectors import (
    CATALOG_PAGE_SIZE,
    base_products,
    category_scope,
    curated_catalog_products,
    filter_catalog,
    suggest_products,
    filter_groups_for_catalog,
    filters_reset_url,
    parse_catalog_filters,
    pdp_related,
    pdp_set_products,
)
from src.commerce.forms import BuyNowForm, CallbackForm, style_form
from src.commerce.wishlist import sku_set
from src.content.form_labels import apply_labels
from src.content.models import ContactForms, HomeBlock, HomeCollection, Review
from src.core.seo import _page_number


def _filters_active(parsed):
    return bool(
        parsed["q"]
        or parsed["in_stock"]
        or parsed["attrs"]
        or parsed["categories"]
        or parsed.get("menu")
    )


def _panel_open(parsed):
    return bool(parsed["attrs"] or parsed["categories"] or parsed.get("menu"))


def _active_filter_count(parsed):
    count = len(parsed["categories"]) + len(parsed.get("menu") or [])
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


def _catalog_context(request, category=None):
    parsed = parse_catalog_filters(request.GET)
    qs = base_products()
    if category:
        qs = qs.filter(category_id__in=category_scope(category))
    facet_base = qs
    filtered = filter_catalog(qs, parsed)
    active = _filters_active(parsed)
    use_curated = not category and not active and not parsed["sort"]
    if use_curated:
        all_products = curated_catalog_products()
    else:
        all_products = list(filtered)
    show_all = request.GET.get("all") == "1"
    total_count = len(all_products)
    page_number = _page_number(request.GET.get("page")) or 1
    page_past_end = False
    if show_all:
        products = all_products
        page_number = 1
        start = 0
    else:
        start = (page_number - 1) * CATALOG_PAGE_SIZE
        if page_number > 1 and start >= total_count:
            page_number = 1
            start = 0
            page_past_end = True
        products = all_products[start : start + CATALOG_PAGE_SIZE]
    has_more = not show_all and start + CATALOG_PAGE_SIZE < total_count
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
        "menu_facets": menu_facets(),
        "panel_open": _panel_open(parsed),
        "filters_open": _panel_open(parsed),
        "subcategories": subcategories,
        "filters_reset_url": filters_reset_url(request),
        "filters_active": bool(
            parsed["in_stock"] or parsed["attrs"] or parsed["categories"] or parsed.get("menu")
        ),
        "active_filter_count": _active_filter_count(parsed),
        "crumbs": category.chain() if category else [],
        "has_more": has_more,
        "show_all": show_all,
        "catalog_page": page_number,
        "load_all_url": _load_all_url(request),
        "catalog_cta": block.cta if block else "",
        "wishlist_skus": sku_set(request),
        "use_curated": use_curated,
        "page_past_end": page_past_end,
    }


def _catalog_url_without_page(request):
    query = request.GET.copy()
    query.pop("page", None)
    encoded = query.urlencode()
    if encoded:
        return f"{request.path}?{encoded}"
    return request.path


def catalog(request, slug=None):
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
    context = _catalog_context(request, category)
    past_end = context.pop("page_past_end", False)
    if past_end:
        target = _catalog_url_without_page(request)
        if request.headers.get("HX-Request"):
            response = render(request, "catalog/_results.html", context)
            response["HX-Push-Url"] = target
            return response
        return redirect(target)
    template = "catalog/_results.html" if request.headers.get("HX-Request") else "catalog/list.html"
    return render(request, template, context)


def product_detail(request, slug):
    product = get_object_or_404(base_products(), slug=slug)
    if not product.is_active:
        raise Http404
    collection = (
        HomeCollection.objects.filter(product=product, is_active=True)
        .exclude(slug="")
        .order_by("sort", "id")
        .first()
    )
    if collection is not None:
        return redirect(collection.get_absolute_url())
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
            "menu_crumb": accessory_crumb(product),
        },
    )


def _suggest_price(product, currency):
    amount = product.price_eur if currency == "eur" else product.price_uah
    whole = int(Decimal(amount or 0).quantize(Decimal("1")))
    text = f"{whole:,}".replace(",", " ")
    return f"{text} €" if currency == "eur" else f"{text} UAH"


def _suggest_image(product):
    if product.card_image:
        return product.card_image.url
    cover = product.cover
    if cover is not None and cover.image:
        return cover.image.url
    return ""


def catalog_suggest(request):
    products = suggest_products(request.GET.get("q") or "")
    collections = {
        row.product_id: row.get_absolute_url()
        for row in HomeCollection.objects.filter(
            product_id__in=[product.pk for product in products],
            is_active=True,
        ).exclude(slug="")
    }
    currency = request.session.get("currency", "uah")
    if currency not in {"uah", "eur"}:
        currency = "uah"
    items = []
    for product in products:
        items.append(
            {
                "name": product.name,
                "url": collections.get(product.pk) or product.get_absolute_url(),
                "price": _suggest_price(product, currency),
                "image": _suggest_image(product),
            }
        )
    response = JsonResponse({"items": items})
    response["X-Robots-Tag"] = "noindex"
    return response
