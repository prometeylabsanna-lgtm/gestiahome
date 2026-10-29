"""Відео головної на формі блока, після якого воно стоїть на сторінці.

Порядок у templates/content/home.html: категорії, потім video;
переваги, потім video_2. Рядки HomeBlock не видаляються.
"""

from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.utils import flatten_fieldsets
from django.db import models

from src.content.admin_limits import tighten
from src.content.models import HomeBlock
from src.core.admin_base import AdminImagePreviewWidget
from src.core.admin_lang import UK_TAB

VIDEO_FIELDS = ("media_kind", "image", "image_mobile", "video", "poster")
FIELD_PREFIX = "page_video_"
HINTS = {
    "image": "1442×871 px. JPG або PNG.",
    "image_mobile": "390×735 px. JPG або PNG.",
    "video": "MP4 або WEBM.",
}


def video_field_name(name):
    return f"{FIELD_PREFIX}{name}"


class PageVideoMixin:
    """Поля сусіднього HomeBlock у fieldset цієї форми."""

    page_video_key = ""
    page_video_sort = 0
    page_video_title = ""
    page_video_description = ""

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        video_fields = tuple(video_field_name(name) for name in VIDEO_FIELDS)
        for index, (title, opts) in enumerate(fieldsets):
            if title != UK_TAB:
                continue
            fields = tuple(opts.get("fields", ())) + video_fields
            merged = {**opts, "fields": fields}
            bits = [opts.get("description") or "", self.page_video_description or ""]
            if self.page_video_title:
                bits.insert(0, self.page_video_title)
            description = "\n".join(part for part in bits if part).strip()
            if description:
                merged["description"] = description
            fieldsets[index] = (title, merged)
            return fieldsets
        fieldsets.append(
            (
                UK_TAB,
                {
                    "classes": ("tab",),
                    "description": self.page_video_description,
                    "fields": video_fields,
                },
            )
        )
        return fieldsets

    def get_form(self, request, obj=None, change=False, **kwargs):
        requested = kwargs.get("fields")
        if requested is None:
            requested = flatten_fieldsets(super().get_fieldsets(request, obj))
        kwargs["fields"] = [name for name in requested if not str(name).startswith(FIELD_PREFIX)]
        form_class = super().get_form(request, obj, change=change, **kwargs)
        video = self._video_block(create=False)
        admin = self

        class WithPageVideo(form_class):
            def __init__(self, *args, **form_kwargs):
                super().__init__(*args, **form_kwargs)
                for name in VIDEO_FIELDS:
                    db_field = HomeBlock._meta.get_field(name)
                    formfield = ModelAdmin.formfield_for_dbfield(admin, db_field, request)
                    if isinstance(db_field, models.ImageField) and formfield is not None:
                        formfield.widget = AdminImagePreviewWidget()
                    tighten(formfield, None, HINTS.get(name, ""))
                    formfield.initial = getattr(video, name)
                    self.fields[video_field_name(name)] = formfield

        return WithPageVideo

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        video = self._video_block(create=True)
        for name in VIDEO_FIELDS:
            db_field = HomeBlock._meta.get_field(name)
            value = form.cleaned_data.get(video_field_name(name))
            if isinstance(db_field, models.FileField):
                db_field.save_form_data(video, value)
            else:
                setattr(video, name, value if value is not None else "")
        video.key = self.page_video_key
        video.save()

    def _video_block(self, create):
        found = HomeBlock.objects.filter(key=self.page_video_key).first()
        if found is not None:
            return found
        if not create:
            return HomeBlock(key=self.page_video_key, sort=self.page_video_sort)
        block, _created = HomeBlock.objects.get_or_create(
            key=self.page_video_key,
            defaults={"sort": self.page_video_sort},
        )
        return block
