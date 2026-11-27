from django.db import models

from src.content.models import SingletonModel
from src.core.utils import localized


class ErrorPage(SingletonModel):
    cache_key = "error_page_v1"
    title_uk = models.CharField("Заголовок", max_length=200, blank=True)
    title_en = models.CharField("Заголовок (EN)", max_length=200, blank=True)
    title_fr = models.CharField("Заголовок (FR)", max_length=200, blank=True)
    text_uk = models.CharField("Текст", max_length=400, blank=True)
    text_en = models.CharField("Текст (EN)", max_length=400, blank=True)
    text_fr = models.CharField("Текст (FR)", max_length=400, blank=True)
    note_en = models.CharField("Примітка (EN)", max_length=400, blank=True)
    note_fr = models.CharField("Примітка (FR)", max_length=400, blank=True)
    button_uk = models.CharField("Кнопка", max_length=80, blank=True)
    button_en = models.CharField("Кнопка (EN)", max_length=80, blank=True)
    button_fr = models.CharField("Кнопка (FR)", max_length=80, blank=True)

    class Meta:
        verbose_name = "Сторінка помилки 500"
        verbose_name_plural = "Сторінка помилки 500"

    def __str__(self):
        return "Сторінка помилки 500"

    @property
    def title(self):
        return localized(self, "title")

    @property
    def text(self):
        return localized(self, "text")

    @property
    def button(self):
        return localized(self, "button")
