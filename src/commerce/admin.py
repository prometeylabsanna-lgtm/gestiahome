from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from src.commerce.models import Inquiry, Order, OrderItem
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
    )
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    actions = ("confirm_payment_manually",)

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
        for order in queryset:
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                if (
                    locked.payment_method != Order.Payment.CARD
                    or locked.payment_status == Order.PayStatus.PAID
                ):
                    skipped += 1
                    continue
                locked.payment_status = Order.PayStatus.PAID
                locked.paid_at = timezone.now()
                locked.payment_raw_status = "manual"
                locked.save(
                    update_fields=["payment_status", "paid_at", "payment_raw_status"]
                )
                self.log_change(request, locked, "Оплату підтверджено вручну")
                confirmed += 1
        self.message_user(
            request,
            f"Підтверджено: {confirmed}, пропущено: {skipped}",
            messages.INFO,
        )


@admin.register(Inquiry)
class InquiryAdmin(GestiaModelAdmin):
    list_display = ("created_at", "kind", "name", "email", "phone", "sku", "product_name")
    list_filter = ("kind",)
    search_fields = ("name", "email", "phone", "sku", "product_name", "message")
    readonly_fields = ("created_at",)
