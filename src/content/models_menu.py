"""Групи каталогу в мегаменю / мобільному меню."""

from django.db import models
from django.urls import reverse

from src.core.utils import localized


class MenuGroup(models.Model):
    title_uk = models.CharField("Назва", max_length=120)
    title_en = models.CharField("Назва (EN)", max_length=120, blank=True)
    sort = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)
    open_by_default = models.BooleanField(
        "Розгорнута за замовчуванням",
        default=False,
        help_text="У меню відкрита лише одна група одночасно.",
    )

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Група меню"
        verbose_name_plural = "Меню каталогу"

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        return localized(self, "title")


class MenuGroupItem(models.Model):
    group = models.ForeignKey(
        MenuGroup,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="Група",
    )
    label_uk = models.CharField("Підпис", max_length=160)
    label_en = models.CharField("Підпис (EN)", max_length=160, blank=True)
    collection = models.ForeignKey(
        "content.HomeCollection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_items",
        verbose_name="Колекція",
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_items",
        verbose_name="Категорія",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показувати", default=True)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункти меню"

    def __str__(self):
        return self.label_uk

    @property
    def label(self):
        return localized(self, "label")

    def get_href(self):
        if self.collection_id:
            return self.collection.get_absolute_url()
        if self.category_id:
            return self.category.get_absolute_url()
        return reverse("catalog")
