from django.contrib import admin


class SlugAdminMixin:
    """Слаг не редагується в формі: новий запис генерує модель, існуючий лише показуємо."""

    auto_slug = True
    slug_source_field = "name_uk"

    @admin.display(description="Адреса сторінки")
    def slug_address(self, obj):
        return getattr(obj, "slug", None) or "—"

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        if "slug" not in exclude:
            exclude.append("slug")
        return exclude

    def get_readonly_fields(self, request, obj=None):
        readonly = [name for name in super().get_readonly_fields(request, obj) if name != "slug"]
        if obj and getattr(obj, "pk", None) and _has_slug(obj) and "slug_address" not in readonly:
            readonly.append("slug_address")
        return readonly

    def get_prepopulated_fields(self, request, obj=None):
        return {}

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        return _rewrite_slug_fieldsets(fieldsets, obj)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        return _rewrite_slug_fields(fields, obj)


def set_form_help(form_class, name: str, text: str) -> None:
    """Readonly fields read help from the form meta, not from the widget."""
    help_texts = dict(form_class._meta.help_texts or {})
    help_texts[name] = text
    form_class._meta.help_texts = help_texts


def _has_slug(obj) -> bool:
    return any(field.name == "slug" for field in obj._meta.concrete_fields)


def _rewrite_slug_fields(fields, obj):
    show_address = bool(obj and getattr(obj, "pk", None))
    out = []
    for name in fields:
        if name == "slug":
            if show_address:
                out.append("slug_address")
            continue
        out.append(name)
    return type(fields)(out) if isinstance(fields, tuple) else out


def _rewrite_slug_fieldsets(fieldsets, obj):
    rewritten = []
    for title, opts in fieldsets:
        new_opts = dict(opts)
        if "fields" in new_opts:
            new_opts["fields"] = _rewrite_slug_fields(new_opts["fields"], obj)
        rewritten.append((title, new_opts))
    return tuple(rewritten)
