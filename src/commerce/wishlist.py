from django.db.models import Prefetch

from src.catalog.models import Product, ProductImage

SESSION_KEY = "wishlist"
MAX_ITEMS = 99


def _raw(request) -> list[str]:
    data = request.session.get(SESSION_KEY)
    if not isinstance(data, list):
        return []
    return [str(sku) for sku in data if sku]


def _save(request, items: list[str]):
    request.session[SESSION_KEY] = items[:MAX_ITEMS]
    request.session.modified = True


def item_count(request) -> int:
    return len(_raw(request))


def contains(request, sku: str) -> bool:
    return sku in _raw(request)


def sku_set(request) -> set[str]:
    return set(_raw(request))


def add(request, sku: str) -> bool:
    items = _raw(request)
    if sku in items:
        return False
    items.append(sku)
    _save(request, items)
    return True


def remove(request, sku: str) -> bool:
    items = _raw(request)
    if sku not in items:
        return False
    items = [value for value in items if value != sku]
    _save(request, items)
    return True


def toggle(request, sku: str) -> bool:
    """Return True when the SKU is present after the toggle."""
    if contains(request, sku):
        remove(request, sku)
        return False
    add(request, sku)
    return True


def clear(request):
    _save(request, [])


def products(request):
    skus = _raw(request)
    if not skus:
        return []
    found = (
        Product.objects.filter(sku__in=skus, is_active=True)
        .prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("sort", "id")))
    )
    by_sku = {product.sku: product for product in found}
    return [by_sku[sku] for sku in skus if sku in by_sku]
