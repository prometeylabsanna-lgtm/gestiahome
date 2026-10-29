from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from src.content.admin_limits import tighten
from src.content.models import HomeBlock
from src.core.admin_base import GestiaModelAdmin
from src.core.admin_tinymce import force_tinymce, tinymce_widget

VIDEO_HINT = "MP4 або WEBM."
_TINY = frozenset({"text_uk", "text_en"})


class KeyedBlockAdmin(GestiaModelAdmin):
    block_key = ""
    default_sort = 0
    text_limits = {}
    image_hints = {}
    tiny_fields = _TINY

    def get_queryset(self, request):
        return super().get_queryset(request).filter(key=self.block_key)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = HomeBlock.objects.filter(key=self.block_key).first()
        if obj is None:
            obj = HomeBlock.objects.create(key=self.block_key, sort=self.default_sort)
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)

    def save_model(self, request, obj, form, change):
        obj.key = self.block_key
        super().save_model(request, obj, form, change)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tiny_fields:
            kwargs["widget"] = tinymce_widget(short=True)
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        hint = self.image_hints.get(db_field.name, "")
        if db_field.name == "video":
            hint = VIDEO_HINT
        return tighten(formfield, self.text_limits.get(db_field.name), hint)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        force_tinymce(form, self.tiny_fields, short=True)
        for name, limit in self.text_limits.items():
            if name in form.base_fields:
                tighten(form.base_fields[name], limit)
        return form
