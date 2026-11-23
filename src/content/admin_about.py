from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.admin_limits import tighten
from src.content.proxies import (
    AboutApproach,
    AboutClosing,
    AboutGestia,
    AboutIntro,
    AboutTogether,
    FooterChrome,
)
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget


class _OpenSingleton(GestiaModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        obj = self.model.load()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)


@admin.register(AboutIntro)
class AboutIntroAdmin(_OpenSingleton):
    text_limits = {"title_uk": 40, "title_en": 40}
    tiny_fields = ("intro_text_uk", "intro_text_en", "intro_text_fr")
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "intro_text_uk",
            "intro_photo_left",
            "intro_photo_left_alt_uk",
            "intro_photo_main",
            "intro_photo_main_alt_uk",
            "seo_title_uk",
            "seo_description_uk",
        ),
        en_fields=(
            "title_en",
            "intro_text_en",
            "intro_photo_left_alt_en",
            "intro_photo_main_alt_en",
            "seo_title_en",
            "seo_description_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form


@admin.register(AboutGestia)
class AboutGestiaAdmin(_OpenSingleton):
    tiny_fields = ("gestia_text_uk", "gestia_text_en", "gestia_text_fr")
    fieldsets = language_tabs(
        uk_fields=(
            "gestia_quote_uk",
            "gestia_plate",
            "gestia_plate_alt_uk",
            "gestia_photo",
            "gestia_photo_alt_uk",
            "gestia_text_uk",
        ),
        en_fields=(
            "gestia_quote_en",
            "gestia_plate_alt_en",
            "gestia_photo_alt_en",
            "gestia_text_en",
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form


@admin.register(AboutApproach)
class AboutApproachAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("approach_text_uk",),
        en_fields=("approach_text_en",),
    )


@admin.register(AboutTogether)
class AboutTogetherAdmin(_OpenSingleton):
    tiny_fields = ("together_text_uk", "together_text_en", "together_text_fr")
    fieldsets = language_tabs(
        uk_fields=("together_photo", "together_photo_alt_uk", "together_text_uk"),
        en_fields=("together_photo_alt_en", "together_text_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form


@admin.register(AboutClosing)
class AboutClosingAdmin(_OpenSingleton):
    tiny_fields = ("closing_text_uk", "closing_text_en", "closing_text_fr")
    text_limits = {"cta_uk": 40, "cta_en": 40}
    fieldsets = language_tabs(
        uk_fields=("closing_text_uk", "cta_uk"),
        en_fields=("closing_text_en", "cta_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        return tighten(formfield, self.text_limits.get(db_field.name))

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form


@admin.register(FooterChrome)
class FooterChromeAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("footer_note_uk", "credit_uk"),
        en_fields=("footer_note_en", "credit_en"),
    )
