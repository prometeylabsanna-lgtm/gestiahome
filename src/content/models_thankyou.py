from django.db import models

from src.content.models import SingletonModel
from src.core.utils import localized


EMAIL_SUBJECT_DEFAULTS = {
    "uk": "Замовлення {number}",
    "en": "Order {number}",
    "fr": "Commande {number}",
}
EMAIL_BODY_DEFAULTS = {
    "uk": (
        "Дякуємо за замовлення, найближчим часом наш консультант зв'яжеться з вами. "
        "Номер: {number}"
    ),
    "en": (
        "Thank you for the order. A consultant will contact you shortly. "
        "Number: {number}"
    ),
    "fr": (
        "Merci pour votre commande. Un conseiller vous contactera sous peu. "
        "Numéro : {number}"
    ),
}
_NUMBER_HELP = "Плейсхолдер {number} підставляється безпечно."


class ThankYouPage(SingletonModel):
    cache_key = "thankyou_page_v2"
    rich_text_fields = (
        "order_text_uk",
        "order_text_en",
        "order_text_nonum_uk",
        "order_text_nonum_en",
        "contact_text_uk",
        "contact_text_en",
        "order_text_fr",
        "order_text_nonum_fr",
        "contact_text_fr",
    )
    order_title_uk = models.CharField("Заголовок замовлення", max_length=200, blank=True)
    order_title_en = models.CharField("Заголовок замовлення (EN)", max_length=200, blank=True)
    order_title_fr = models.CharField("Заголовок замовлення (FR)", max_length=200, blank=True)
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
    order_text_fr = models.TextField(
        "Текст із номером (FR)",
        blank=True,
        help_text="Placeholder {number} is substituted safely.",
    )
    order_text_nonum_uk = models.TextField("Текст без номера", blank=True)
    order_text_nonum_en = models.TextField("Текст без номера (EN)", blank=True)
    order_text_nonum_fr = models.TextField("Текст без номера (FR)", blank=True)
    link_uk = models.CharField("Підпис посилання", max_length=80, blank=True)
    link_en = models.CharField("Підпис посилання (EN)", max_length=80, blank=True)
    link_fr = models.CharField("Підпис посилання (FR)", max_length=80, blank=True)
    contact_title_uk = models.CharField("Заголовок повідомлення", max_length=120, blank=True)
    contact_title_en = models.CharField("Заголовок повідомлення (EN)", max_length=120, blank=True)
    contact_title_fr = models.CharField("Заголовок повідомлення (FR)", max_length=120, blank=True)
    contact_text_uk = models.TextField("Текст повідомлення", blank=True)
    contact_text_en = models.TextField("Текст повідомлення (EN)", blank=True)
    contact_text_fr = models.TextField("Текст повідомлення (FR)", blank=True)
    email_subject_uk = models.CharField(
        "Тема листа",
        max_length=200,
        blank=True,
        help_text=_NUMBER_HELP,
    )
    email_subject_en = models.CharField(
        "Тема листа (EN)",
        max_length=200,
        blank=True,
        help_text=_NUMBER_HELP,
    )
    email_subject_fr = models.CharField(
        "Тема листа (FR)",
        max_length=200,
        blank=True,
        help_text=_NUMBER_HELP,
    )
    email_body_uk = models.TextField("Текст листа", blank=True, help_text=_NUMBER_HELP)
    email_body_en = models.TextField("Текст листа (EN)", blank=True, help_text=_NUMBER_HELP)
    email_body_fr = models.TextField("Текст листа (FR)", blank=True, help_text=_NUMBER_HELP)

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
