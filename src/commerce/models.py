from django.db import models
from django.utils.translation import gettext_lazy as _

from src.catalog.models import Product


class Order(models.Model):
    class Source(models.TextChoices):
        CART = "cart", _("Кошик")
        BUY_NOW = "buy_now", _("Замовити одразу")

    class Delivery(models.TextChoices):
        BRANCH = "np_branch", _("Нова пошта — відділення")
        LOCKER = "np_locker", _("Нова пошта — поштамат")
        COURIER = "np_courier", _("Нова пошта — кур'єр")

    class Payment(models.TextChoices):
        CARD = "card", _("Онлайн карткою")
        ON_DELIVERY = "on_delivery", _("При отриманні")

    class PayStatus(models.TextChoices):
        UNPAID = "unpaid", "Не оплачено"
        AWAITING = "awaiting", "Очікує оплату"
        PAID = "paid", "Оплачено"
        FAILED = "failed", _("Помилка оплати")

    number = models.CharField("Номер", max_length=24, unique=True)
    idempotency_key = models.CharField(
        "Ключ ідемпотентності",
        max_length=64,
        null=True,
        blank=True,
        unique=True,
    )
    source = models.CharField("Джерело", max_length=16, choices=Source.choices)
    customer_name = models.CharField("Ім'я", max_length=120)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)
    language = models.CharField("Мова", max_length=8, default="uk")
    currency = models.CharField("Валюта", max_length=8, default="uah")
    delivery_method = models.CharField("Доставка", max_length=16, choices=Delivery.choices)
    delivery_address = models.CharField("Адреса", max_length=255)
    payment_method = models.CharField("Оплата", max_length=16, choices=Payment.choices)
    payment_status = models.CharField(
        "Стан оплати",
        max_length=16,
        choices=PayStatus.choices,
        default=PayStatus.UNPAID,
    )
    payment_ref = models.CharField(
        "LiqPay order_id",
        max_length=64,
        blank=True,
        default="",
        db_index=True,
    )
    payment_txn = models.CharField("LiqPay payment_id", max_length=64, blank=True, default="")
    payment_raw_status = models.CharField("LiqPay status", max_length=64, blank=True, default="")
    paid_at = models.DateTimeField("Оплачено о", null=True, blank=True)
    total = models.DecimalField("Сума", max_digits=12, decimal_places=2)
    consent = models.BooleanField("Згода", default=False)
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        permissions = [
            ("confirm_payment_manually", "Підтвердити оплату вручну"),
        ]

    def __str__(self):
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    sku = models.CharField("Артикул", max_length=64)
    name = models.CharField("Назва", max_length=200)
    qty = models.PositiveIntegerField("Кількість")
    unit_price = models.DecimalField("Ціна", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Позиція"
        verbose_name_plural = "Позиції"

    def __str__(self):
        return f"{self.sku} × {self.qty}"

    @property
    def line_total(self):
        return self.unit_price * self.qty


class Inquiry(models.Model):
    class Kind(models.TextChoices):
        CALLBACK = "callback", "Заявка на товар"
        CONTACT = "contact", "Зворотний зв'язок"
        WAITLIST = "waitlist", "Святкові бокси (email)"

    kind = models.CharField("Тип", max_length=16, choices=Kind.choices)
    name = models.CharField("Ім'я", max_length=120, blank=True)
    phone = models.CharField("Телефон", max_length=32, blank=True)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Повідомлення", blank=True)
    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    product_name = models.CharField("Назва товару", max_length=200, blank=True)
    sku = models.CharField("Артикул", max_length=64, blank=True)
    consent = models.BooleanField("Згода", default=False)
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"{self.get_kind_display()} · {self.name}"
