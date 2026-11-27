from django.db import models


class NovaPoshtaCity(models.Model):
    ref = models.CharField("Код (Ref)", max_length=64, unique=True)
    name = models.CharField("Назва", max_length=180)
    area = models.CharField("Область", max_length=160, blank=True, default="")
    search_text = models.CharField("Пошук", max_length=360)

    class Meta:
        ordering = ["name"]
        verbose_name = "Місто Нової пошти"
        verbose_name_plural = "Міста Нової пошти"
        indexes = [
            models.Index(fields=["search_text"]),
        ]

    def __str__(self):
        return self.name


class NovaPoshtaWarehouse(models.Model):
    class Kind(models.TextChoices):
        BRANCH = "branch", "Відділення"
        LOCKER = "locker", "Поштамат"

    ref = models.CharField("Код (Ref)", max_length=64, unique=True)
    number = models.CharField("Номер", max_length=16, blank=True, default="")
    label = models.CharField("Назва", max_length=400)
    city_ref = models.CharField("Місто ref", max_length=64, blank=True, default="")
    city_name = models.CharField("Місто", max_length=180, blank=True, default="")
    address = models.CharField("Адреса", max_length=400, blank=True, default="")
    kind = models.CharField("Тип", max_length=16, choices=Kind.choices, default=Kind.BRANCH)
    is_active = models.BooleanField("Активне", default=True)
    search_text = models.CharField("Пошук", max_length=900)

    class Meta:
        ordering = ["city_name", "number"]
        verbose_name = "Відділення Нової пошти"
        verbose_name_plural = "Відділення Нової пошти"
        indexes = [
            models.Index(fields=["kind", "is_active", "city_ref"]),
            models.Index(fields=["kind", "is_active", "number"]),
        ]

    def __str__(self):
        return self.label


class NovaPoshtaSyncState(models.Model):
    last_synced_at = models.DateTimeField("Остання синхронізація", null=True, blank=True)
    warehouse_count = models.PositiveIntegerField("Відділень", default=0)
    city_count = models.PositiveIntegerField("Міст", default=0)

    class Meta:
        verbose_name = "Синхронізація Нової пошти"
        verbose_name_plural = "Синхронізація Нової пошти"

    def __str__(self):
        if self.last_synced_at is None:
            return "Ще не синхронізовано"
        return self.last_synced_at.strftime("%Y-%m-%d %H:%M")
