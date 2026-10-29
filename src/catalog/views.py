from django.http import Http404
from django.shortcuts import get_object_or_404, render

from src.catalog.models import Category
from src.catalog.selectors import (
    base_products,
    catalog_bands,
    category_scope,
    filter_catalog,
    filter_categories,
    filter_frame_cards,
    filter_groups_for_catalog,
    filters_reset_url,
    mobile_frame_groups,
    parse_catalog_filters,
    pdp_related,
    pdp_set_products,
)
from src.commerce.forms import BuyNowForm, CallbackForm, style_form
from src.content.form_labels import apply_labels
from src.content.models import ContactForms, HomeBlock, Review


def _filters_active(parsed):
    return bool(parsed["q"] or parsed["in_stock"] or parsed["attrs"] or parsed["categories"])


def _panel_open(parsed):
    return bool(parsed["attrs"] or parsed["categories"])


def _catalog_context(request, category=None):
    parsed = parse_catalog_filters(request.GET)
    qs = base_products()
    if category:
        qs = qs.filter(category_id__in=category_scope(category))
    facet_base = qs
    products = filter_catalog(qs, parsed)
    active = _filters_active(parsed)
    # Mosaic is only for the root catalog browse; category/filter views use the grid.
    use_mosaic = not category and not active
    bands = catalog_bands() if use_mosaic else []
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
        "filter_cards": filter_frame_cards() if use_mosaic else [],
        "mobile_groups": mobile_frame_groups() if use_mosaic else [],
        "panel_open": _panel_open(parsed),
        "subcategories": subcategories,
        "filters_reset_url": filters_reset_url(request),
        "crumbs": category.chain() if category else [],
        "catalog_bands": bands,
        "show_mosaic": use_mosaic,
        "catalog_cta": block.cta if block else "",
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
        },
    )
