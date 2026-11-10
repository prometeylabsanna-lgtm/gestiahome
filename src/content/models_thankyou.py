from django.db import models

from src.content.models import SingletonModel
from src.core.utils import localized


class ThankYouPage(SingletonModel):
    cache_key = "thankyou_page_v1"
    rich_text_fields = (
        "order_text_uk",
        "order_text_en",
        "order_text_nonum_uk",
        "order_text_nonum_en",
        "contact_text_uk",
        "contact_text_en",
    )
    order_title_uk = models.CharField("Заголовок замовлення", max_length=200, blank=True)
    order_title_en = models.CharField("Заголовок замовлення (EN)", max_length=200, blank=True)
    order_text_uk = models.TextField(
        "Текст із номером",
        blank=True,
        help_text="Плейсхолдер {number} підставляється безпечно.",
    )
    order_text_en = models.TextField(
        "Текст із номером (EN)",
        blank=True,
        help_text="Placeholder {number} is substituted safely.",
    )
    order_text_nonum_uk = models.TextField("Текст без номера", blank=True)
    order_text_nonum_en = models.TextField("Текст без номера (EN)", blank=True)
    link_uk = models.CharField("Підпис посилання", max_length=80, blank=True)
    link_en = models.CharField("Підпис посилання (EN)", max_length=80, blank=True)
    contact_title_uk = models.CharField("Заголовок повідомлення", max_length=120, blank=True)
    contact_title_en = models.CharField("Заголовок повідомлення (EN)", max_length=120, blank=True)
    contact_text_uk = models.TextField("Текст повідомлення", blank=True)
    contact_text_en = models.TextField("Текст повідомлення (EN)", blank=True)

    class Meta:
        verbose_name = "Сторінка подяки"
        verbose_name_plural = "Сторінка подяки"

    def __str__(self):
        return "Сторінка подяки"

    @property
    def order_title(self):
        return localized(self, "order_title")

    @property
    def order_text(self):
        return localized(self, "order_text")

    @property
    def order_text_nonum(self):
        return localized(self, "order_text_nonum")

    @property
    def link(self):
        return localized(self, "link")

    @property
    def contact_title(self):
        return localized(self, "contact_title")

    @property
    def contact_text(self):
        return localized(self, "contact_text")
