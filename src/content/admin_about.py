from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.admin_limits import tighten
from src.content.models import AboutPage
from src.content.models_about import AboutGalleryItem, AboutPopularSlot
from src.content.proxies import (
    AboutBanner,
    AboutGallery,
    AboutIntro,
    AboutPopularBlock,
    AboutReviewsBlock,
    AboutStory,
    FooterChrome,
)
from src.core.admin_base import GestiaModelAdmin, GestiaStackedInline, GestiaTabularInline
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget


class _OpenSingleton(GestiaModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)


class AboutGalleryInline(GestiaTabularInline):
    model = AboutGalleryItem
    extra = 0
    max_num = 3
    fields = ("slot", "sort", "media_kind", "image", "video", "poster")


class AboutPopularSlotInline(GestiaTabularInline):
    model = AboutPopularSlot
    extra = 0
    tab = True
    verbose_name = "Товар"
    verbose_name_plural = "Товари"
    ordering_field = "sort"
    hide_ordering_field = True
    autocomplete_fields = ("product",)
    fields = ("product", "sort")


@admin.register(AboutIntro)
class AboutIntroAdmin(_OpenSingleton):
    text_limits = {"title_uk": 24, "title_en": 24}
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "lead_uk",
            "crumb_uk",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "title_en",
            "lead_en",
            "crumb_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))


@admin.register(AboutGallery)
class AboutGalleryAdmin(_OpenSingleton):
    inlines = (AboutGalleryInline,)
    fieldsets = language_tabs(
        uk_fields=(),
        en_fields=(),
        uk_description="Нижче — три кадри галереї (фото або відео).",
    )


@admin.register(AboutStory)
class AboutStoryAdmin(_OpenSingleton):
    tiny_fields = ("body_uk", "body_en")
    fieldsets = language_tabs(
        uk_fields=("story_label_uk", "body_uk"),
        en_fields=("story_label_en", "body_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return formfield

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form


@admin.register(AboutBanner)
class AboutBannerAdmin(_OpenSingleton):
    image_hints = {
        "image": "Одна картинка для десктопу і мобільного, у макеті 1442×871. JPG або PNG.",
    }
    fieldsets = language_tabs(
        uk_fields=("media_kind", "image", "video", "poster"),
        en_fields=(),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        hint = self.image_hints.get(db_field.name, "")
        if formfield is not None and hint:
            formfield.help_text = hint
        return formfield


@admin.register(AboutReviewsBlock)
class AboutReviewsAdmin(_OpenSingleton):
    text_limits = {"reviews_title_uk": 16, "reviews_title_en": 16}
    fieldsets = language_tabs(
        uk_fields=("reviews_title_uk",),
        en_fields=("reviews_title_en",),
        uk_description="Заголовок блоку відгуків на сторінці «Про нас». Список — окремим підменю.",
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))


@admin.register(AboutPopularBlock)
class AboutPopularAdmin(_OpenSingleton):
    inlines = (AboutPopularSlotInline,)
    text_limits = {
        "popular_title_uk": 24,
        "popular_title_en": 24,
        "popular_cta_uk": 28,
        "popular_cta_en": 28,
    }
    fieldsets = language_tabs(
        uk_fields=("popular_title_uk", "popular_cta_uk"),
        en_fields=("popular_title_en", "popular_cta_en"),
        uk_description="Оберіть товари для блоку популярних на «Про нас» (як на головній).",
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))


# Сумісність зі старими тестами/імпортами.
AboutPicksAdmin = AboutPopularAdmin


@admin.register(FooterChrome)
class FooterChromeAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("footer_note_uk", "credit_uk"),
        en_fields=("footer_note_en", "credit_en"),
    )


class AboutPageAdmin(_OpenSingleton):
    inlines = (AboutGalleryInline, AboutPopularSlotInline)
    text_limits = {"title_uk": 24, "title_en": 24}
    tiny_fields = ("body_uk", "body_en")
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "lead_uk",
            "crumb_uk",
            "story_label_uk",
            "body_uk",
            "media_kind",
            "image",
            "video",
            "poster",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "title_en",
            "lead_en",
            "crumb_en",
            "story_label_en",
            "body_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )
