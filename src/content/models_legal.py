from django.db import models

from src.core.utils import localized


class LegalPage(models.Model):
    class Key(models.TextChoices):
        OFFER = "offer", "Публічний договір"
        PRIVACY = "privacy", "Політика конфіденційності"
        COOKIES = "cookies", "Політика cookies"
        SHIPPING = "shipping", "Доставка та оплата"

    rich_text_fields = ("body_uk", "body_en")
    key = models.CharField("Сторінка", max_length=16, choices=Key.choices, unique=True)
    title_uk = models.CharField("Заголовок", max_length=200)
    title_en = models.CharField("Заголовок (EN)", max_length=200, blank=True)
    body_uk = models.TextField("Текст", blank=True)
    body_en = models.TextField("Текст (EN)", blank=True)
    seo_title_uk = models.CharField("SEO title", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO title (EN)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO description", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO description (EN)", max_length=300, blank=True)
    updated_on = models.DateField("Дата оновлення", null=True, blank=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        verbose_name = "Юридична сторінка"
        verbose_name_plural = "Юридичні сторінки"

    def __str__(self):
        return self.title_uk or self.key

    @property
    def title(self):
        return localized(self, "title")

    @property
    def body(self):
        return localized(self, "body")
