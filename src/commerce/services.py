import secrets
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Case, CharField, F, Value, When
from django.utils import timezone
from django.utils.translation import get_language, gettext as _

from src.catalog.models import Product
from src.commerce.models import Inquiry, Order, OrderItem
from src.commerce.notify import notify_inquiry, notify_order
from src.commerce.stock_hold import apply_new_hold

NUMBER_ATTEMPTS = 5


class OrderValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def unavailable_message(name) -> str:
    label = str(name or "").strip() or "—"
    return _("Товар «%(name)s» зараз відсутній. Приберіть його з кошика.") % {"name": label}


def insufficient_stock_message(name, left) -> str:
    label = str(name or "").strip() or "—"
    return _("Товару «%(name)s» залишилось лише %(left)s шт.") % {"name": label, "left": left}


def normalize_idempotency_key(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    return raw[:64]


def _number() -> str:
    stamp = timezone.now().strftime("%y%m%d")
    return f"GS{stamp}-{secrets.token_hex(3).upper()}"


def _pay_status(method: str) -> str:
    if method == Order.Payment.CARD:
        return Order.PayStatus.AWAITING
    return Order.PayStatus.UNPAID


def _locked_rows(rows, currency):
    skus = [row["sku"] for row in rows]
    locked = {
        product.sku: product
        for product in Product.objects.select_for_update().filter(sku__in=skus).order_by("pk")
    }
    priced = []
    for row in rows:
        product = locked.get(row["sku"])
        if product is None or not product.is_active or product.stock_status == Product.Stock.OUT:
            name = product.name_uk if product is not None else row.get("name") or row["sku"]
            raise OrderValidationError(unavailable_message(name))
        unit = product.amount(currency)
        qty = int(row["qty"])
        if qty > product.stock_qty:
            raise OrderValidationError(insufficient_stock_message(product.name_uk, product.stock_qty))
        priced.append(
            {
                "pk": product.pk,
                "sku": product.sku,
                "name": row.get("name") or product.name_uk,
                "qty": qty,
                "unit": unit,
                "line_total": unit * qty,
            }
        )
    return priced


def _take_stock(rows):
    needed = {}
    for row in rows:
        pk = row["pk"]
        needed[pk] = needed.get(pk, 0) + int(row["qty"])
    for pk, qty in needed.items():
        taken = Product.objects.filter(pk=pk, stock_qty__gte=qty).update(
            stock_qty=F("stock_qty") - qty,
            stock_status=Case(
                When(stock_qty=qty, then=Value(Product.Stock.OUT)),
                default=F("stock_status"),
                output_field=CharField(max_length=16),
            ),
        )
        if taken == 1:
            continue
        product = Product.objects.filter(pk=pk).first()
        name = product.name_uk if product is not None else ""
        left = product.stock_qty if product is not None else 0
        raise OrderValidationError(insufficient_stock_message(name, left))


def _insert_order(*, source, customer, currency, language, total, idempotency_key):
    for _attempt in range(NUMBER_ATTEMPTS):
        number = _number()
        if Order.objects.filter(number=number).exists():
            continue
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    number=number,
                    idempotency_key=idempotency_key,
                    source=source,
                    customer_name=customer["name"],
                    phone=customer["phone"],
                    email=customer.get("email", ""),
                    language=language or get_language() or "uk",
                    currency=currency,
                    delivery_method=customer["delivery_method"],
                    delivery_address=customer["address"],
                    np_city_ref=customer.get("np_city_ref") or "",
                    np_warehouse_ref=customer.get("np_warehouse_ref") or "",
                    payment_method=customer["payment_method"],
                    payment_status=_pay_status(customer["payment_method"]),
                    total=total,
                    consent=True,
                )
        except IntegrityError:
            if idempotency_key:
                existing = Order.objects.filter(idempotency_key=idempotency_key).first()
                if existing is not None:
                    return existing, True
            continue
        return order, False
    raise IntegrityError("order number collision")


@transaction.atomic
def create_order(*, source, customer, rows, currency, language, idempotency_key=None):
    key = normalize_idempotency_key(idempotency_key)
    if key:
        existing = Order.objects.filter(idempotency_key=key).first()
        if existing is not None:
            return existing
    priced = _locked_rows(rows, currency)
    total = sum((row["line_total"] for row in priced), Decimal("0"))
    order, replayed = _insert_order(
        source=source,
        customer=customer,
        currency=currency,
        language=language,
        total=total,
        idempotency_key=key,
    )
    if replayed:
        return order
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                sku=row["sku"],
                name=row["name"],
                qty=row["qty"],
                unit_price=row["unit"],
            )
            for row in priced
        ]
    )
    _take_stock(priced)
    apply_new_hold(order, customer["payment_method"])
    order_id = order.pk
    transaction.on_commit(lambda oid=order_id: notify_order(oid))
    return order


def row_from_product(product: Product, qty: int, currency: str):
    unit = product.amount(currency)
    return {
        "sku": product.sku,
        "name": product.name_uk,
        "qty": qty,
        "unit": unit,
        "line_total": unit * qty,
    }


@transaction.atomic
def create_inquiry(*, kind, name, phone, consent, message="", email="", sku=""):
    product = None
    product_name = ""
    if sku:
        product = Product.objects.filter(sku=sku, is_active=True).first()
        if product:
            product_name = product.name_uk
            sku = product.sku
        else:
            sku = ""
    inquiry = Inquiry.objects.create(
        kind=kind,
        name=name,
        phone=phone,
        email=email,
        message=message,
        product=product,
        product_name=product_name,
        sku=sku,
        consent=consent,
    )
    inquiry_id = inquiry.pk
    transaction.on_commit(lambda iid=inquiry_id: notify_inquiry(iid))
    return inquiry
