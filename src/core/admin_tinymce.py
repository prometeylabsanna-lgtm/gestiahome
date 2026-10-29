"""TinyMCE for multi-sentence admin fields, including custom ModelForms."""

from __future__ import annotations

from django.conf import settings
from tinymce.widgets import TinyMCE


def tinymce_widget(*, short=True):
    config = settings.TINYMCE_SHORT_CONFIG if short else settings.TINYMCE_DEFAULT_CONFIG
    return TinyMCE(mce_attrs=config)


def force_tinymce(form, field_names, *, short=True):
    """Replace widgets on declared form fields (wins over Meta.widgets / __init__)."""
    names = set(field_names or ())
    if not names:
        return form
    fields = form.base_fields if isinstance(form, type) else form.fields
    for name in names:
        field = fields.get(name)
        if field is None:
            continue
        attrs = dict(getattr(field.widget, "attrs", {}) or {})
        widget = tinymce_widget(short=short)
        widget.attrs.update(attrs)
        field.widget = widget
    return form


def rich_field_names(model) -> tuple[str, ...]:
    names = getattr(model, "rich_text_fields", None)
    if names:
        return tuple(names)
    return ()
