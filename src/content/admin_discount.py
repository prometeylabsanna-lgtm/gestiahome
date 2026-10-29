from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from tinymce.widgets import TinyMCE

from src.content.models_discount import DiscountModal
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_lang import language_tabs

_EN_HINT = "Якщо порожньо — на сайті лишається український текст."


class DiscountModalAdmin(GestiaModelAdmin):
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
        if db_field.name in {"text_uk", "text_en"}:
            kwargs["widget"] = TinyMCE(mce_attrs=settings.TINYMCE_SHORT_CONFIG)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None and db_field.name in {"title_en", "text_en", "button_en"}:
            formfield.help_text = _EN_HINT
        return formfield


admin.site.register(DiscountModal, DiscountModalAdmin)
