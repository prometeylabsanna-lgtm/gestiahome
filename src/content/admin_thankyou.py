from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.proxies import ThankYouContact, ThankYouOrder
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


@admin.register(ThankYouOrder)
class ThankYouOrderAdmin(_OpenSingleton):
    tiny_fields = (
        "order_text_uk",
        "order_text_en",
        "order_text_nonum_uk",
        "order_text_nonum_en",
    )
    fieldsets = language_tabs(
        uk_fields=(
            "order_title_uk",
            "order_text_uk",
            "order_text_nonum_uk",
            "link_uk",
        ),
        en_fields=(
            "order_title_en",
            "order_text_en",
            "order_text_nonum_en",
            "link_en",
        ),
        uk_description="У тексті з номером використовуйте плейсхолдер {number}.",
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


@admin.register(ThankYouContact)
class ThankYouContactAdmin(_OpenSingleton):
    tiny_fields = ("contact_text_uk", "contact_text_en")
    fieldsets = language_tabs(
        uk_fields=("contact_title_uk", "contact_text_uk"),
        en_fields=("contact_title_en", "contact_text_en"),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form
