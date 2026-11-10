from src.content.models import HomeCollection


def _active_addon_products(collections):
    seen = set()
    products = []
    for collection in collections:
        for product in collection.addons.all():
            if not product.is_active or product.id in seen:
                continue
            seen.add(product.id)
            products.append(product)
    return products


def _collections_for_products(product_ids):
    if not product_ids:
        return HomeCollection.objects.none()
    return (
        HomeCollection.objects.filter(is_active=True, product_id__in=product_ids)
        .prefetch_related("addons")
        .order_by("sort", "id")
    )


def _all_active_collections():
    return (
        HomeCollection.objects.filter(is_active=True)
        .prefetch_related("addons")
        .order_by("sort", "id")
    )


def page_suggest_addons(rows, *, limit=3):
    """Addons for cart page «Доповнити сет»: first 3 not already in cart."""
    cart_skus = {row["sku"] for row in rows}
    product_ids = [row["product"].id for row in rows if row.get("product") is not None]
    pool = _active_addon_products(_collections_for_products(product_ids))
    if not pool:
        pool = _active_addon_products(_all_active_collections())
    result = []
    for product in pool:
        if product.sku in cart_skus:
            continue
        result.append(product)
        if len(result) >= limit:
            break
    return result


def drawer_addon_items(focus_product, cart_skus):
    """Addons for cart drawer; includes in-cart items for «Додано» state."""
    if focus_product is not None:
        pool = _active_addon_products(_collections_for_products([focus_product.id]))
    else:
        pool = []
    if not pool:
        pool = _active_addon_products(_all_active_collections())
    return [
        {"product": product, "in_cart": product.sku in cart_skus, "sku": product.sku}
        for product in pool
    ]


def focus_cart_row(rows, sku):
    if not sku:
        return None
    for row in rows:
        if row["sku"] == sku:
            return row
    return None
