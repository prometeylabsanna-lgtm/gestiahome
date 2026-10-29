from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from src.content.media import IMAGE_VALIDATOR
from src.content.models import SingletonModel
from src.core.fields import WebPImageField
from src.core.utils import localized

_LINK_HINT = "Адреса на сайті, наприклад /katalog/."


def safe_public_link(value: str) -> str:
    raw = (value or "").strip()
    if not raw or len(raw) > 300 or "\\" in raw or any(ch in raw for ch in "\r\n\t"):
        return ""
    if raw.startswith("/") and not raw.startswith("//"):
        return raw
    parts = urlsplit(raw)
    if parts.scheme in {"http", "https"} and parts.netloc and not parts.username and not parts.password:
        return raw
    return ""


def validate_public_link(value: str) -> None:
    if value and not safe_public_link(value):
        raise ValidationError("Вкажіть адресу на сайті або посилання http(s).")


class DiscountModal(SingletonModel):
    """Попап знижки / waitlist (email) на сайті."""

    cache_key = "discount_modal_v1"
    rich_text_fields = ("text_uk", "text_en")

    enabled = models.BooleanField("Показувати вікно", default=False)
    waitlist_title_uk = models.CharField("Заголовок вікна", max_length=56, blank=True)
    waitlist_title_en = models.CharField("Заголовок вікна (EN)", max_length=56, blank=True)
    waitlist_p1_uk = models.CharField("Перший абзац", max_length=160, blank=True)
    waitlist_p1_en = models.CharField("Перший абзац (EN)", max_length=160, blank=True)
    waitlist_p2_uk = models.CharField("Другий абзац", max_length=120, blank=True)
    waitlist_p2_en = models.CharField("Другий абзац (EN)", max_length=120, blank=True)
    waitlist_p3_uk = models.CharField("Третій абзац", max_length=140, blank=True)
    waitlist_p3_en = models.CharField("Третій абзац (EN)", max_length=140, blank=True)
    waitlist_email_uk = models.CharField("Підказка email", max_length=20, blank=True)
    waitlist_email_en = models.CharField("Підказка email (EN)", max_length=20, blank=True)
    waitlist_consent_uk = models.CharField("Текст згоди", max_length=72, blank=True)
    waitlist_consent_en = models.CharField("Текст згоди (EN)", max_length=72, blank=True)
    waitlist_privacy_uk = models.CharField("Посилання на політику", max_length=36, blank=True)
    waitlist_privacy_en = models.CharField("Посилання на політику (EN)", max_length=36, blank=True)
    waitlist_button_uk = models.CharField("Кнопка", max_length=24, blank=True)
    waitlist_button_en = models.CharField("Кнопка (EN)", max_length=24, blank=True)
    waitlist_thanks_title_uk = models.CharField("Заголовок після надсилання", max_length=16, blank=True)
    waitlist_thanks_title_en = models.CharField("Заголовок після надсилання (EN)", max_length=16, blank=True)
    waitlist_thanks_text_uk = models.CharField("Текст після надсилання", max_length=90, blank=True)
    waitlist_thanks_text_en = models.CharField("Текст після надсилання (EN)", max_length=90, blank=True)
    # Legacy CTA fields (застарілі; лишаються для сумісності).
    title_uk = models.CharField("Заголовок", max_length=80, blank=True)
    title_en = models.CharField("Заголовок (EN)", max_length=80, blank=True)
    text_uk = models.TextField("Текст", blank=True)
    text_en = models.TextField("Текст (EN)", blank=True)
    button_uk = models.CharField("Кнопка CTA", max_length=40, blank=True)
    button_en = models.CharField("Кнопка CTA (EN)", max_length=40, blank=True)
    link = models.CharField(
        "Посилання кнопки",
        max_length=300,
        blank=True,
        validators=[validate_public_link],
        help_text=_LINK_HINT,
    )
    image = WebPImageField(
        "Фон вікна",
        upload_to="discount/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Необов’язково. Фонове зображення попапа. JPG або PNG.",
    )
    delay_seconds = models.PositiveSmallIntegerField(
        "Затримка перед показом, с",
        default=15,
        validators=[MinValueValidator(0), MaxValueValidator(600)],
    )
    shows_per_session = models.PositiveSmallIntegerField(
        "Показів за один візит",
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(99)],
    )

    class Meta:
        verbose_name = "Знижка"
        verbose_name_plural = "Знижка"

    def __str__(self):
        return "Знижка"

    def clean(self):
        super().clean()
        self.link = (self.link or "").strip()
        validate_public_link(self.link)

    @property
    def title(self):
        return localized(self, "waitlist_title") or localized(self, "title")

    @property
    def text(self):
        body = localized(self, "text")
        if body:
            return body
        chunks = [
            localized(self, "waitlist_title"),
            localized(self, "waitlist_p1"),
            localized(self, "waitlist_p2"),
            localized(self, "waitlist_p3"),
        ]
        return "\n\n".join(part.strip() for part in chunks if (part or "").strip())

    @property
    def button(self):
        return localized(self, "waitlist_button") or localized(self, "button")

    @property
    def public_url(self) -> str:
        return safe_public_link(self.link)

    @property
    def delay_ms(self) -> int:
        seconds = self.delay_seconds if self.delay_seconds is not None else 15
        return max(0, min(int(seconds), 600)) * 1000

    @property
    def show_limit(self) -> int:
        raw = self.shows_per_session if self.shows_per_session is not None else 1
        return max(0, min(int(raw), 99))
