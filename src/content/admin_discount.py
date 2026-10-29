from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.models_discount import DiscountModal
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs
from src.core.admin_tinymce import force_tinymce, tinymce_widget

_EN_HINT = "Якщо порожньо — на сайті лишається український текст."


class DiscountModalAdmin(GestiaModelAdmin):
    tiny_fields = ("text_uk", "text_en")
    fieldsets = language_tabs(
        uk_fields=(
            "enabled",
            "delay_seconds",
            "shows_per_session",
            "title_uk",
            "text_uk",
            "button_uk",
            "link",
            "image",
        ),
        en_fields=("title_en", "text_en", "button_en"),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and db_field.name in {"title_en", "text_en", "button_en"}:
            formfield.help_text = _EN_HINT
        return formfield

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        return form


admin.site.register(DiscountModal, DiscountModalAdmin)
