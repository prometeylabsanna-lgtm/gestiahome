from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.admin_limits import tighten
from src.content.models import AboutPage
from src.content.models_about import AboutGalleryItem, AboutPick
from src.content.proxies import FooterChrome
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

    tiny_fields = ("body_uk", "body_en")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        for name, limit in self.text_limits.items():
            if name in form.base_fields:
                tighten(form.base_fields[name], limit)
        return form


@admin.register(FooterChrome)
class FooterChromeAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("footer_note_uk", "credit_uk", "developer_note_uk"),
        en_fields=("footer_note_en", "credit_en", "developer_note_en"),
    )
