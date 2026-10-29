"""Упорядковані категорії та товари на головній."""

from django.db import models


class HomeCategorySlot(models.Model):
    block = models.ForeignKey(
        "content.HomeBlock",
        related_name="category_slots",
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        "catalog.Category",
        related_name="home_slots",
        on_delete=models.CASCADE,
        verbose_name="Категорія",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        constraints = [
            models.UniqueConstraint(fields=["block", "category"], name="home_category_slot_uniq"),
        ]
        verbose_name = "Категорія на головній"
        verbose_name_plural = "Категорії на головній"

    def __str__(self):
        return str(self.category)


class HomePopularSlot(models.Model):
    block = models.ForeignKey(
        "content.HomeBlock",
        related_name="popular_slots",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        "catalog.Product",
        related_name="home_popular_slots",
        on_delete=models.CASCADE,
        verbose_name="Товар",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        constraints = [
            models.UniqueConstraint(fields=["block", "product"], name="home_popular_slot_uniq"),
        ]
        verbose_name = "Популярний товар"
        verbose_name_plural = "Популярні товари"

    def __str__(self):
        return str(self.product)
