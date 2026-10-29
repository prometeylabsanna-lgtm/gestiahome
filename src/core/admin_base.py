from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.widgets import UnfoldAdminImageFieldWidget

IMAGE_HELP = "JPG або PNG, довша сторона до 2560 px."
_PREVIEW_ORDER = ("image", "card_image", "logo")


class AdminImagePreviewWidget(UnfoldAdminImageFieldWidget):
    template_name = "admin/widgets/gestia_image_preview.html"

    def __init__(self, attrs=None):
        merged = dict(attrs or {})
        merged["accept"] = "image/*"
        super().__init__(attrs=merged)


class ImagePreviewMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.ImageField):
            kwargs["widget"] = AdminImagePreviewWidget
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, models.ImageField) and formfield is not None and not formfield.help_text:
            formfield.help_text = IMAGE_HELP
        return formfield


class GestiaModelAdmin(ImagePreviewMixin, ModelAdmin):
    formfield_overrides = {
        models.ImageField: {"widget": AdminImagePreviewWidget},
    }

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if _image_fields(self.model) and "image_thumb" not in display:
            display.insert(1 if display else 0, "image_thumb")
        return display

    @admin.display(description="Фото")
    def image_thumb(self, obj):
        url = preview_url(obj)
        if not url:
            return "—"
        return format_html('<img src="{}" alt="" class="gestia-admin-thumb">', url)


class GestiaTabularInline(ImagePreviewMixin, TabularInline):
    pass


class GestiaStackedInline(ImagePreviewMixin, StackedInline):
    pass


def preview_url(obj) -> str:
    names = _image_fields(type(obj))
    preferred = [name for name in _PREVIEW_ORDER if name in names]
    ordered = preferred + [name for name in names if name not in preferred]
    for name in ordered:
        file = getattr(obj, name, None)
        if not file:
            continue
        try:
            url = file.url
        except (ValueError, AttributeError):
            continue
        if url:
            return url
    return ""


def _image_fields(model) -> list[str]:
    return [field.name for field in model._meta.concrete_fields if isinstance(field, models.ImageField)]
