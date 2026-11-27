import hashlib
from decimal import Decimal

from django.db.models import Prefetch

from src.catalog.models import Product, ProductImage
from src.catalog.storefront import prefetch_public_collections
from src.core.utils import format_money

SESSION_KEY = "cart"
MAX_QTY = 99


def _raw(request):
    data = request.session.get(SESSION_KEY)
    if not isinstance(data, dict):
        data = {}
    return data


def _save(request, data):
    request.session[SESSION_KEY] = data
    request.session.modified = True


def item_count(request) -> int:
    return sum(int(qty) for qty in _raw(request).values())


def _limit(stock_qty):
    if stock_qty is None:
        return MAX_QTY
    return min(MAX_QTY, max(int(stock_qty), 0))


def set_qty(request, sku: str, qty: int, stock_qty=None):
    data = _raw(request)
    if qty <= 0:
        data.pop(sku, None)
    else:
        capped = min(int(qty), _limit(stock_qty))
        if capped <= 0:
            data.pop(sku, None)
        else:
            data[sku] = capped
    _save(request, data)


def add(request, sku: str, qty: int = 1, stock_qty=None):
    data = _raw(request)
    current = int(data.get(sku, 0))
    capped = min(current + max(int(qty), 1), _limit(stock_qty))
    if capped <= 0:
        data.pop(sku, None)
    else:
        data[sku] = capped
    _save(request, data)


def clear(request):
    _save(request, {})


def lines(request, currency: str):
    data = _raw(request)
    if not data:
        request._cart_removed = 0
        return [], Decimal("0")
    products = Product.objects.filter(sku__in=list(data.keys())).prefetch_related(
        Prefetch("images", queryset=ProductImage.objects.order_by("sort", "id")),
        prefetch_public_collections(),
    )
    by_sku = {product.sku: product for product in products}
    rows = []
    total = Decimal("0")
    removed = []
    for sku, qty in data.items():
        product = by_sku.get(sku)
        if product is None or not product.is_active:
            removed.append(sku)
            continue
        qty = int(qty)
        unit = product.amount(currency)
        line_total = unit * qty
        total += line_total
        out_of_stock = product.stock_status == Product.Stock.OUT
        rows.append(
            {
                "product": product,
                "sku": sku,
                "qty": qty,
                "unit": unit,
                "unit_label": format_money(unit, currency),
                "line_label": format_money(line_total, currency),
                "line_total": line_total,
                "out_of_stock": out_of_stock,
                "over_stock": qty > product.stock_qty and not out_of_stock,
            }
        )
    if removed:
        for sku in removed:
            data.pop(sku, None)
        _save(request, data)
    request._cart_removed = len(removed)
    return rows, total


def signature(rows) -> str:
    parts = sorted(f"{row['sku']}:{row['qty']}:{row['unit']}" for row in rows)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
