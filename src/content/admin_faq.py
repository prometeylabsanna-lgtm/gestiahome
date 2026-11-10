from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.models_faq import FaqItem
from src.content.proxies import FaqContact, FaqHeader, FaqSeo
from src.core.admin_base import GestiaModelAdmin
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


@admin.register(FaqHeader)
class FaqHeaderAdmin(_OpenSingleton):
    tiny_fields = ("title_uk", "title_en")
    fieldsets = language_tabs(
        uk_fields=(
            "title_uk",
            "crumb_uk",
            "image",
            "image_alt_uk",
        ),
        en_fields=(
            "title_en",
            "crumb_en",
            "image_alt_en",
        ),
        uk_description="У заголовку можна <br> для переносу рядка, як у макеті.",
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


@admin.register(FaqItem)
class FaqItemAdmin(GestiaModelAdmin):
    list_display = ("question_uk", "sort", "is_active")
    list_editable = ("sort", "is_active")
    list_display_links = ("question_uk",)
    ordering = ("sort", "id")
    exclude = ("page",)
    tiny_fields = ("answer_uk", "answer_en")
    fieldsets = language_tabs(
        uk_fields=("question_uk", "answer_uk", "sort", "is_active"),
        en_fields=("question_en", "answer_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=False)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=False)
        return form

    def save_model(self, request, obj, form, change):
        if obj.page_id is None:
            from src.content.models_faq import FaqPage

            obj.page = FaqPage.load()
        super().save_model(request, obj, form, change)


@admin.register(FaqContact)
class FaqContactAdmin(_OpenSingleton):
    tiny_fields = ("contact_text_uk", "contact_text_en")
    fieldsets = language_tabs(
        uk_fields=("contact_title_uk", "contact_text_uk"),
        en_fields=("contact_title_en", "contact_text_en"),
        uk_description="Email та Instagram беруться з налаштувань сайту.",
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


@admin.register(FaqSeo)
class FaqSeoAdmin(_OpenSingleton):
    fieldsets = language_tabs(
        uk_fields=("seo_title_uk", "seo_description_uk"),
        en_fields=("seo_title_en", "seo_description_en"),
    )
