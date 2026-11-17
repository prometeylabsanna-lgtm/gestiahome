from django.db import models

from src.content.media import IMAGE_VALIDATOR
from src.content.models import SingletonModel
from src.core.fields import WebPImageField
from src.core.utils import localized


class FaqPage(SingletonModel):
    cache_key = "faq_page_v1"
    rich_text_fields = (
        "title_uk",
        "title_en",
        "contact_text_uk",
        "contact_text_en",
    )
    title_uk = models.TextField("Заголовок", blank=True)
    title_en = models.TextField("Заголовок (EN)", blank=True)
    crumb_uk = models.CharField("Крихітка", max_length=40, blank=True)
    crumb_en = models.CharField("Крихітка (EN)", max_length=40, blank=True)
    image = WebPImageField(
        "Фото",
        upload_to="faq/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Лише wide ≥900. Близько 4:3. JPG або PNG.",
    )
    image_alt_uk = models.CharField("Alt фото", max_length=200, blank=True)
    image_alt_en = models.CharField("Alt фото (EN)", max_length=200, blank=True)
    contact_title_uk = models.CharField("Заголовок контактів", max_length=80, blank=True)
    contact_title_en = models.CharField("Заголовок контактів (EN)", max_length=80, blank=True)
    contact_text_uk = models.TextField("Текст контактів", blank=True)
    contact_text_en = models.TextField("Текст контактів (EN)", blank=True)
    seo_title_uk = models.CharField("SEO title", max_length=200, blank=True)
    seo_title_en = models.CharField("SEO title (EN)", max_length=200, blank=True)
    seo_description_uk = models.CharField("SEO description", max_length=300, blank=True)
    seo_description_en = models.CharField("SEO description (EN)", max_length=300, blank=True)

    class Meta:
        verbose_name = "Сторінка FAQ"
        verbose_name_plural = "Сторінка FAQ"

    def __str__(self):
        return "Актуальні питання"

    @property
    def title(self):
        return localized(self, "title")

    @property
    def crumb(self):
        return localized(self, "crumb")

    @property
    def image_alt(self):
        return localized(self, "image_alt")

    @property
    def contact_title(self):
        return localized(self, "contact_title")

    @property
    def contact_text(self):
        return localized(self, "contact_text")

    @property
    def seo_title(self):
        return localized(self, "seo_title") or " ".join(
            str(self.title or "").replace("<br>", " ").replace("<br/>", " ").split()
        )

    @property
    def seo_description(self):
        return localized(self, "seo_description")


class FaqItem(models.Model):
    rich_text_fields = ("answer_uk", "answer_en")
    page = models.ForeignKey(
        FaqPage,
        related_name="items",
        on_delete=models.CASCADE,
    )
    question_uk = models.CharField("Питання", max_length=200)
    question_en = models.CharField("Питання (EN)", max_length=200, blank=True)
    answer_uk = models.TextField("Відповідь", blank=True)
    answer_en = models.TextField("Відповідь (EN)", blank=True)
    sort = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Питання FAQ"
        verbose_name_plural = "Питання FAQ"

    def __str__(self):
        return self.question_uk

    @property
    def question(self):
        return localized(self, "question")

    @property
    def answer(self):
        return localized(self, "answer")
