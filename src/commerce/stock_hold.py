"""Резерв залишку карткового замовлення: зняття після відмови або 24 годин."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from src.catalog.models import Product
from src.commerce.models import Order

_STOCK_FIELDS = ("stock_held", "stock_released", "stock_short", "hold_until")


def hold_hours() -> int:
    return int(getattr(settings, "CARD_STOCK_HOLD_HOURS", 24))


def _copy_flags(target, source) -> None:
    for name in _STOCK_FIELDS:
        setattr(target, name, getattr(source, name))


def apply_new_hold(order, payment_method) -> None:
    """Після успішного списання в create_order. Картка має термін, решта — ні."""
    order.stock_held = True
    order.stock_released = False
    order.stock_short = False
    if payment_method == Order.Payment.CARD:
        order.hold_until = timezone.now() + timedelta(hours=hold_hours())
    else:
        order.hold_until = None
    order.save(update_fields=list(_STOCK_FIELDS))


def _needed_by_sku(order) -> dict[str, int]:
    needed: dict[str, int] = {}
    for item in order.items.all():
        sku = item.sku
        needed[sku] = needed.get(sku, 0) + int(item.qty)
    return needed


def _restore(order) -> bool:
    """Повертає штуки. Прапорці змінює в пам'яті, збереження замовлення — на викликачі."""
    if not order.stock_held:
        return False
    needed = _needed_by_sku(order)
    if needed:
        locked_products = list(
            Product.objects.select_for_update().filter(sku__in=list(needed)).order_by("pk")
        )
        for product in locked_products:
            qty = needed.get(product.sku, 0)
            if qty <= 0:
                continue
            product.stock_qty += qty
            product.save(update_fields=["stock_qty"])
    order.stock_held = False
    order.stock_released = True
    order.hold_until = None
    return True


def _item_rows(order):
    items = list(order.items.all())
    if not items:
        return []
    skus = {item.sku for item in items}
    products = {
        product.sku: product
        for product in Product.objects.filter(sku__in=skus, is_active=True)
    }
    if set(products) != skus:
        return None
    return [
        {"pk": products[item.sku].pk, "qty": int(item.qty), "sku": item.sku}
        for item in items
    ]


@transaction.atomic
def release_held_stock(order) -> bool:
    """Один раз повертає залишок, якщо замовлення його ще тримає."""
    locked = Order.objects.select_for_update().get(pk=order.pk)
    changed = _restore(locked)
    if changed:
        locked.save(update_fields=["stock_held", "stock_released", "hold_until"])
    _copy_flags(order, locked)
    return changed


@transaction.atomic
def rehold_stock(order) -> bool:
    """Знову списує залишок після зняття резерву. Легасі без stock_released не чіпає склад."""
    from src.commerce.services import OrderValidationError, _take_stock

    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.stock_held or not locked.stock_released:
        _copy_flags(order, locked)
        return True
    rows = _item_rows(locked)
    if rows is None:
        return False
    if rows:
        pks = sorted({row["pk"] for row in rows})
        list(Product.objects.select_for_update().filter(pk__in=pks).order_by("pk"))
        try:
            with transaction.atomic():
                _take_stock(rows)
        except OrderValidationError:
            return False
    locked.stock_held = True
    locked.stock_released = False
    locked.stock_short = False
    if locked.payment_method == Order.Payment.CARD:
        locked.hold_until = timezone.now() + timedelta(hours=hold_hours())
    else:
        locked.hold_until = None
    locked.save(update_fields=list(_STOCK_FIELDS))
    _copy_flags(order, locked)
    return True


def _expired(order, now) -> bool:
    return (
        order.payment_method == Order.Payment.CARD
        and order.payment_status == Order.PayStatus.AWAITING
        and order.stock_held
        and order.hold_until is not None
        and order.hold_until < now
    )


@transaction.atomic
def _expire_one(pk, now) -> bool:
    locked = (
        Order.objects.select_for_update()
        .filter(pk=pk)
        .first()
    )
    if locked is None or not _expired(locked, now):
        return False
    _restore(locked)
    locked.payment_status = Order.PayStatus.FAILED
    locked.payment_raw_status = "expired"
    locked.save(
        update_fields=[
            "stock_held",
            "stock_released",
            "hold_until",
            "payment_status",
            "payment_raw_status",
        ]
    )
    return True


def release_expired_holds() -> int:
    """Картка, awaiting, термін резерву минув. Кожне замовлення — окрема транзакція."""
    now = timezone.now()
    pks = list(
        Order.objects.filter(
            payment_method=Order.Payment.CARD,
            payment_status=Order.PayStatus.AWAITING,
            stock_held=True,
            hold_until__lt=now,
        ).values_list("pk", flat=True)
    )
    return sum(1 for pk in pks if _expire_one(pk, now))
