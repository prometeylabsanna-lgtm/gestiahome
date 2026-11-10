from urllib.parse import urlencode

from django.db.models import Prefetch, Q

from src.catalog.models import CatalogCell, Category, Product, ProductAttributeGroup, ProductImage

ATTRIBUTE_FILTER_KEYS = (
    ProductAttributeGroup.Slug.STYLE,
    ProductAttributeGroup.Slug.COLOR,
)


def catalog_filter_query_names():
    """GET-параметри, які каталог справді читає для фільтрів."""
    return ("q", "in_stock", "category", *ATTRIBUTE_FILTER_KEYS)


def _ordered_images():
    return Prefetch("images", queryset=ProductImage.objects.order_by("sort", "id"))


def base_products():
    return (
        Product.objects.filter(is_active=True)
        .select_related("category", "category__parent", "product_set")
        .prefetch_related(_ordered_images(), "filter_attrs__group")
    )


def nav_categories():
    roots = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related("children")
        .order_by("sort", "name_uk")
    )
    return [cat for cat in roots if cat.has_public_products]


SORT_CHOICES = (
    ("", "default"),
    ("price_asc", "price_asc"),
    ("price_desc", "price_desc"),
    ("name", "name"),
)
SORT_KEYS = {key for key, _ in SORT_CHOICES}


def parse_catalog_filters(get):
    attrs = {}
    for key in ATTRIBUTE_FILTER_KEYS:
        values = [value for value in get.getlist(key) if value][:12]
        if values:
            attrs[key] = values
    selected = [f"{key}:{value}" for key, values in attrs.items() for value in values]
    categories = [value for value in get.getlist("category") if value][:12]
    sort = (get.get("sort") or "").strip()
    if sort not in SORT_KEYS:
        sort = ""
    return {
        "attrs": attrs,
        "selected": selected,
        "categories": categories,
        "q": (get.get("q") or "").strip()[:80],
        "in_stock": get.get("in_stock") == "1",
        "sort": sort,
    }


def filter_catalog(qs, parsed):
    query = parsed["q"]
    if query:
        qs = qs.filter(
            Q(name_uk__icontains=query)
            | Q(name_en__icontains=query)
            | Q(sku__iexact=query)
        )
    if parsed["categories"]:
        qs = qs.filter(category__slug__in=parsed["categories"])
    for key, values in parsed["attrs"].items():
        qs = qs.filter(filter_attrs__group__slug=key, filter_attrs__slug__in=values)
    if parsed["in_stock"]:
        qs = qs.filter(stock_status=Product.Stock.IN_STOCK)
    qs = qs.distinct()
    sort = parsed.get("sort") or ""
    if sort == "price_asc":
        return qs.order_by("price_uah", "sort", "id")
    if sort == "price_desc":
        return qs.order_by("-price_uah", "sort", "id")
    if sort == "name":
        return qs.order_by("name_uk", "sort", "id")
    return qs.order_by("sort", "id")


def category_scope(category):
    ids = [category.pk]
    ids.extend(category.children.filter(is_active=True).values_list("pk", flat=True))
    return ids


def filter_groups_for_catalog(product_qs):
    del product_qs
    groups = []
    for key in ATTRIBUTE_FILTER_KEYS:
        group = ProductAttributeGroup.objects.filter(slug=key).first()
        if group is None:
            continue
        values = list(group.values.filter(is_filterable=True).order_by("sort", "name_uk"))
        if values:
            groups.append({"group": group, "values": values})
    return groups


def filter_categories():
    return Category.objects.filter(is_active=True, filter_sort__isnull=False).order_by("filter_sort", "name_uk")


def _cells(surface):
    return (
        CatalogCell.objects.filter(surface=surface)
        .select_related("product", "product__category")
        .prefetch_related("product__images")
        .order_by("sort", "band", "id")
    )


def catalog_bands():
    cells = _cells(CatalogCell.Surface.MOSAIC).order_by("band", "sort", "id")
    bands = []
    index = {}
    for cell in cells:
        band = index.get(cell.band)
        if band is None:
            band = {"layout": cell.layout, "grid": [], "feature": []}
            index[cell.band] = band
            bands.append(band)
        key = "feature" if cell.role == CatalogCell.Role.FEATURE else "grid"
        band[key].append(cell)
    return bands


def filter_frame_cards():
    return _cells(CatalogCell.Surface.FILTERS)


def curated_catalog_products():
    """Товари з кураторських клітинок FILTERS (без мозаїки); без товару / неактивні — пропуск."""
    products = []
    for cell in filter_frame_cards():
        product = getattr(cell, "product", None)
        if product is None or not product.is_active:
            continue
        products.append(product)
    return products


CATALOG_PAGE_SIZE = 12


def mobile_frame_groups():
    groups = []
    tiles = []
    for cell in _cells(CatalogCell.Surface.MOBILE):
        if cell.slot in {CatalogCell.Slot.FEATURE, CatalogCell.Slot.FEATURE_TALL}:
            if tiles:
                groups.append({"kind": "tiles", "cells": tiles})
                tiles = []
            groups.append({"kind": cell.slot, "cells": [cell]})
        else:
            tiles.append(cell)
    if tiles:
        groups.append({"kind": "tiles", "cells": tiles})
    return groups


def filters_reset_url(request):
    query = (request.GET.get("q") or "").strip()
    if query:
        return f"{request.path}?{urlencode({'q': query})}"
    return request.path


def pdp_set_products(product):
    if not product.product_set_id:
        return []
    return list(base_products().filter(product_set_id=product.product_set_id).order_by("sort", "id"))


def pdp_related(product):
    manual_ids = list(
        product.related_manual.filter(is_active=True).order_by("sort", "id").values_list("pk", flat=True)
    )
    if manual_ids:
        order = {pk: index for index, pk in enumerate(manual_ids)}
        rows = list(base_products().filter(pk__in=manual_ids))
        rows.sort(key=lambda item: order.get(item.pk, 0))
        return rows
    return related_products(product)


def pdp_mobile_cards():
    return list(
        CatalogCell.objects.filter(surface=CatalogCell.Surface.PDP_MOBILE)
        .select_related("product")
        .order_by("sort", "id")
    )


def same_set(product, limit=4):
    if not product.product_set_id:
        return Product.objects.none()
    return (
        base_products()
        .filter(product_set=product.product_set)
        .exclude(pk=product.pk)[:limit]
    )


def related_products(product, limit=4):
    set_ids = []
    if product.product_set_id:
        set_ids = list(
            product.product_set.products.exclude(pk=product.pk).values_list("pk", flat=True)
        )
    manual = list(
        base_products()
        .filter(pk__in=product.related_manual.filter(is_active=True).values("pk"))
        .exclude(pk__in=set_ids)[:limit]
    )
    if len(manual) >= limit:
        return manual
    attr_ids = list(product.filter_attrs.values_list("pk", flat=True))
    taken = [item.pk for item in manual] + set_ids
    auto = (
        base_products()
        .filter(Q(category=product.category) | Q(filter_attrs__in=attr_ids))
        .exclude(pk=product.pk)
        .exclude(pk__in=taken)
        .distinct()[: limit - len(manual)]
    )
    return manual + list(auto)
