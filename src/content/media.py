"""Спільний вибір: на вітрині або фото, або відео з постером."""

from django.core.validators import FileExtensionValidator
from django.db import models

from src.core.fields import WebPImageField

IMAGE_VALIDATOR = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])
VIDEO_VALIDATOR = FileExtensionValidator(["mp4", "webm"])


class MediaChoice(models.Model):
    class Kind(models.TextChoices):
        PHOTO = "photo", "Фото"
        VIDEO = "video", "Відео"

    media_kind = models.CharField(
        "Що показати",
        max_length=8,
        choices=Kind.choices,
        default=Kind.PHOTO,
        blank=True,
        help_text="Фото — картинка. Відео — MP4 або WEBM.",
    )
    poster = WebPImageField(
        "Постер",
        upload_to="posters/",
        blank=True,
        validators=[IMAGE_VALIDATOR],
        help_text="Кадр до старту відео. Якщо порожньо — береться основне фото.",
    )

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if not self.media_kind:
            self.media_kind = self.Kind.PHOTO

    def save(self, *args, **kwargs):
        if not self.media_kind:
            self.media_kind = self.Kind.PHOTO
        super().save(*args, **kwargs)

    @property
    def shows_video(self):
        video = getattr(self, "video", None)
        return self.media_kind == self.Kind.VIDEO and bool(video)

    @property
    def still_image(self):
        """Основне фото або фото картки (для постера / fallback)."""
        for name in ("image", "card_image"):
            value = getattr(self, name, None)
            if value:
                return value
        return None

    @property
    def poster_src(self):
        if self.poster:
            return self.poster.url
        still = self.still_image
        return still.url if still else ""
