"""Медіа і текст банера головної."""

from django.contrib import admin

from src.content.admin_keyed import KeyedBlockAdmin
from src.content.models import HomeBlock
from src.content.proxies import HomeBannerMedia, HomeBannerText
from src.core.admin_lang import language_tabs

PHOTO_DESK = "1442×871 px. Одна картинка для десктопу і мобільного. JPG або PNG."
MEDIA_HINTS = {
    "image": PHOTO_DESK,
    "poster": "Кадр до старту відео, 1442×871 px. Якщо порожньо — основне фото. JPG або PNG.",
}


class MediaOnlyBlockAdmin(KeyedBlockAdmin):
    image_hints = MEDIA_HINTS
    tiny_fields = ()
    fieldsets = language_tabs(
        uk_fields=("media_kind", "image", "video", "poster"),
        en_fields=(),
    )


@admin.register(HomeBannerMedia)
class HomeBannerMediaAdmin(MediaOnlyBlockAdmin):
    block_key = HomeBlock.Key.HERO
    default_sort = 1


@admin.register(HomeBannerText)
class HomeBannerTextAdmin(KeyedBlockAdmin):
    block_key = HomeBlock.Key.HERO
    default_sort = 1
    tiny_fields = ("text_uk", "text_en", "text_fr")
    text_limits = {
        "title_uk": 64,
        "title_en": 64,
        "text_uk": 200,
        "text_en": 200,
        "cta_uk": 28,
        "cta_en": 28,
        "seo_title_uk": 200,
        "seo_title_en": 200,
        "seo_description_uk": 300,
        "seo_description_en": 300,
    }
    fieldsets = language_tabs(
        uk_fields=("title_uk", "text_uk", "cta_uk", "seo_title_uk", "seo_description_uk"),
        en_fields=("title_en", "text_en", "cta_en", "seo_title_en", "seo_description_en"),
    )
