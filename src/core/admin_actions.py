"""Масові дії адмінки: queryset.update() і повідомлення «Оновлено N записів»."""

from django.contrib import admin, messages

from src.commerce.models import Order


def _update(modeladmin, request, queryset, **fields):
    updated = queryset.update(**fields)
    modeladmin.message_user(request, f"Оновлено {updated} записів", messages.SUCCESS)
    return updated


@admin.action(description="Показати на сайті")
def activate_products(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_active=True)


@admin.action(description="Сховати на сайті")
def deactivate_products(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_active=False)


# Ті самі дії для категорій і колекцій (поле is_active).
show_on_site = activate_products
hide_on_site = deactivate_products


@admin.action(description="Активний: так")
def mark_active_yes(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_active=True)


@admin.action(description="Активний: ні")
def mark_active_no(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_active=False)


@admin.action(description="Хіт: так")
def set_popular(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_popular=True)


@admin.action(description="Хіт: ні")
def unset_popular(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_popular=False)


@admin.action(description="Позначити акцією")
def set_sale(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_sale=True)


@admin.action(description="Зняти акцію")
def unset_sale(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, is_sale=False)


@admin.action(description="Статус: Не оплачено")
def set_order_unpaid(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, payment_status=Order.PayStatus.UNPAID)


@admin.action(description="Статус: Очікує оплату")
def set_order_awaiting(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, payment_status=Order.PayStatus.AWAITING)


@admin.action(description="Статус: Оплачено")
def set_order_paid(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, payment_status=Order.PayStatus.PAID)


@admin.action(description="Статус: Помилка оплати")
def set_order_failed(modeladmin, request, queryset):
    _update(modeladmin, request, queryset, payment_status=Order.PayStatus.FAILED)


PRODUCT_ACTIONS = (
    activate_products,
    deactivate_products,
    mark_active_yes,
    mark_active_no,
    set_popular,
    unset_popular,
    set_sale,
    unset_sale,
)

CATEGORY_ACTIONS = (show_on_site, hide_on_site)
COLLECTION_ACTIONS = (show_on_site, hide_on_site)
ORDER_STATUS_ACTIONS = (
    set_order_unpaid,
    set_order_awaiting,
    set_order_paid,
    set_order_failed,
)
