from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from tinymce.widgets import TinyMCE

from src.content.admin_limits import tighten
from src.content.models import AboutPage
from src.content.models_about import AboutGalleryItem, AboutPick
from src.content.proxies import FooterChrome
from src.core.admin_base import GestiaModelAdmin, GestiaStackedInline, GestiaTabularInline
from src.core.admin_lang import language_tabs


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
    fields = ("slot", "sort", "media_kind", "image", "image_mobile", "video", "poster")


class AboutPickInline(GestiaStackedInline):
    model = AboutPick
    extra = 0
    max_num = 2
    fieldsets = language_tabs(
        uk_fields=("sort", "title_uk", "price", "slug", "modifier", "image"),
        en_fields=("title_en",),
    )


@admin.register(AboutPage)
class AboutPageAdmin(_OpenSingleton):
    inlines = (AboutGalleryInline, AboutPickInline)
    text_limits = {"title_uk": 24, "title_en": 24}
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "lead_uk",
            "crumb_uk",
            "story_label_uk",
            "body_uk",
            "media_kind",
            "image",
            "image_mobile",
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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in {"body_uk", "body_en"}:
            kwargs["widget"] = TinyMCE(mce_attrs=settings.TINYMCE_DEFAULT_CONFIG)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))


@admin.register(FooterChrome)
class FooterChromeAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("footer_note_uk", "credit_uk", "developer_note_uk"),
        en_fields=("footer_note_en", "credit_en", "developer_note_en"),
    )
