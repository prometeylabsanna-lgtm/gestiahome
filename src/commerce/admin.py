from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from src.commerce.models import (
    Inquiry,
    NovaPoshtaCity,
    NovaPoshtaSyncState,
    NovaPoshtaWarehouse,
    Order,
    OrderItem,
)
from src.commerce.stock_hold import rehold_stock
from src.core.admin_actions import ORDER_STATUS_ACTIONS
from src.core.admin_base import GestiaModelAdmin, GestiaTabularInline


class OrderItemInline(GestiaTabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("sku", "name", "qty", "unit_price")
    can_delete = False


@admin.register(Order)
class OrderAdmin(GestiaModelAdmin):
    list_display = (
        "number",
        "source",
        "customer_name",
        "phone",
        "total",
        "currency",
        "payment_status",
        "stock_short",
        "created_at",
    )
    list_filter = ("source", "payment_status", "payment_method", "delivery_method", "currency")
    search_fields = ("number", "customer_name", "phone", "email", "items__sku")
    readonly_fields = (
        "number",
        "created_at",
        "total",
        "payment_ref",
        "payment_txn",
        "payment_raw_status",
        "paid_at",
        "stock_short",
    )
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    actions = ("confirm_payment_manually",) + ORDER_STATUS_ACTIONS

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.payment_method == Order.Payment.CARD:
            for name in ("payment_status", "payment_method", "currency"):
                if name not in fields:
                    fields.append(name)
        return fields

    def has_confirm_payment_manually_permission(self, request):
        return request.user.has_perm("commerce.confirm_payment_manually")

    @admin.action(
        permissions=["confirm_payment_manually"],
        description="Підтвердити оплату вручну",
    )
    def confirm_payment_manually(self, request, queryset):
        confirmed = 0
        skipped = 0
        short = 0
        for order in queryset:
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                if (
                    locked.payment_method != Order.Payment.CARD
                    or locked.payment_status == Order.PayStatus.PAID
                ):
                    skipped += 1
                    continue
                if locked.stock_released and not locked.stock_held:
                    if not rehold_stock(locked):
                        short += 1
                        skipped += 1
                        continue
                    locked.refresh_from_db()
                locked.payment_status = Order.PayStatus.PAID
                locked.paid_at = timezone.now()
                locked.payment_raw_status = "manual"
                locked.save(
                    update_fields=["payment_status", "paid_at", "payment_raw_status"]
                )
                self.log_change(request, locked, "Оплату підтверджено вручну")
                confirmed += 1
        text = f"Підтверджено: {confirmed}, пропущено: {skipped}"
        if short:
            text = f"{text}. Немає залишку: {short}"
        self.message_user(request, text, messages.INFO)


class _ReadOnlyCatalogAdmin(GestiaModelAdmin):
    def has_module_permission(self, request):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NovaPoshtaWarehouse)
class NovaPoshtaWarehouseAdmin(_ReadOnlyCatalogAdmin):
    list_display = ("number", "label", "city_name", "kind", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("number", "label", "address", "city_name", "ref")
    readonly_fields = (
        "ref",
        "number",
        "label",
        "city_ref",
        "city_name",
        "address",
        "kind",
        "is_active",
        "search_text",
    )


@admin.register(NovaPoshtaCity)
class NovaPoshtaCityAdmin(_ReadOnlyCatalogAdmin):
    list_display = ("name", "area", "ref")
    search_fields = ("name", "area", "ref")
    readonly_fields = ("ref", "name", "area", "search_text")


@admin.register(NovaPoshtaSyncState)
class NovaPoshtaSyncStateAdmin(_ReadOnlyCatalogAdmin):
    list_display = ("last_synced_at", "warehouse_count", "city_count")
    readonly_fields = ("last_synced_at", "warehouse_count", "city_count")


@admin.register(Inquiry)
class InquiryAdmin(GestiaModelAdmin):
    list_display = ("created_at", "kind", "name", "email", "phone", "sku", "product_name")
    list_filter = ("kind",)
    search_fields = ("name", "email", "phone", "sku", "product_name", "message")
    readonly_fields = ("created_at",)
