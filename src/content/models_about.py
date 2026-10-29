from django.db import models

from src.content.media import IMAGE_VALIDATOR, VIDEO_VALIDATOR, MediaChoice
from src.core.fields import WebPImageField

GALLERY_HINT = "Близько 1090×1440 px. JPG або PNG."


class AboutGalleryItem(MediaChoice):
    class Slot(models.TextChoices):
        A = "a", "Фото 1"
        B = "b", "Фото 2"
        C = "c", "Фото 3"

    page = models.ForeignKey(
        "content.AboutPage",
        related_name="gallery",
        on_delete=models.CASCADE,
    )
    slot = models.CharField("Місце", max_length=8, choices=Slot.choices)
    image = WebPImageField(
        "Фото",
        upload_to="about/gallery/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text=GALLERY_HINT,
    )
    image_mobile = WebPImageField(
        "Фото (застаріле)",
        upload_to="about/gallery/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Не використовується. Залишено для сумісності.",
    )
    video = models.FileField(
        "Відео",
        upload_to="about/video/",
        blank=True,
        validators=[VIDEO_VALIDATOR],
        help_text="MP4 або WEBM.",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        constraints = [
            models.UniqueConstraint(fields=["page", "slot"], name="about_gallery_slot"),
        ]
        verbose_name = "Фото на сторінці «Про нас»"
        verbose_name_plural = "Фото на сторінці «Про нас»"

    def __str__(self):
        return self.get_slot_display()


class AboutPopularSlot(models.Model):
    page = models.ForeignKey(
        "content.AboutPage",
        related_name="popular_slots",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        "catalog.Product",
        related_name="about_popular_slots",
        on_delete=models.CASCADE,
        verbose_name="Товар",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        constraints = [
            models.UniqueConstraint(fields=["page", "product"], name="about_popular_slot_uniq"),
        ]
        verbose_name = "Популярний товар (Про нас)"
        verbose_name_plural = "Популярні товари (Про нас)"

    def __str__(self):
        return str(self.product)


class AboutPick(models.Model):
    """Застарілі ручні картки; адмінка використовує AboutPopularSlot."""

    class Modifier(models.TextChoices):
        SHIFT = "shift", "Зі зсувом"
        COVER = "cover", "Звичайне"

    page = models.ForeignKey(
        "content.AboutPage",
        related_name="picks",
        on_delete=models.CASCADE,
    )
    title_uk = models.CharField("Назва", max_length=40)
    title_en = models.CharField("Назва (EN)", max_length=40, blank=True)
    price = models.CharField("Ціна на картці", max_length=16)
    slug = models.CharField(
        "Адреса товару",
        max_length=80,
        help_text="Як у посиланні на товар.",
    )
    modifier = models.CharField(
        "Вигляд",
        max_length=8,
        choices=Modifier.choices,
        default=Modifier.SHIFT,
    )
    image = WebPImageField(
        "Фото",
        upload_to="about/picks/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Картка близько 200×226. JPG або PNG.",
    )
    sort = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "Картка під відгуками"
        verbose_name_plural = "Картки під відгуками"

    def __str__(self):
        return self.title_uk

    @property
    def title(self):
        from src.core.utils import localized

        return localized(self, "title")
