from django.db import models

from src.content.models import SingletonModel
from src.core.utils import localized


class ContactsPage(SingletonModel):
    cache_key = "contacts_page_v1"
    title_uk = models.CharField("Заголовок", max_length=80, blank=True)
    title_en = models.CharField("Заголовок (EN)", max_length=80, blank=True)
    title_fr = models.CharField("Заголовок (FR)", max_length=80, blank=True)
    seo_title_uk = models.CharField("SEO title", max_length=80, blank=True)
    seo_title_en = models.CharField("SEO title (EN)", max_length=80, blank=True)
    seo_title_fr = models.CharField("SEO title (FR)", max_length=80, blank=True)
    seo_description_uk = models.CharField("SEO description", max_length=320, blank=True)
    seo_description_en = models.CharField("SEO description (EN)", max_length=320, blank=True)
    seo_description_fr = models.CharField("SEO description (FR)", max_length=320, blank=True)
    form_title_uk = models.CharField("Заголовок форми", max_length=80, blank=True)
    form_title_en = models.CharField("Заголовок форми (EN)", max_length=80, blank=True)
    form_title_fr = models.CharField("Заголовок форми (FR)", max_length=80, blank=True)

    class Meta:
        verbose_name = "Сторінка контактів"
        verbose_name_plural = "Сторінка контактів"

    def __str__(self):
        return "Сторінка контактів"

    @property
    def title(self):
        return localized(self, "title")

    @property
    def seo_title(self):
        return localized(self, "seo_title")

    @property
    def seo_description(self):
        return localized(self, "seo_description")

    @property
    def form_title(self):
        return localized(self, "form_title")
