from django.core.validators import MaxLengthValidator

from src.core.html_sanitize import visible_max_length


def tighten(formfield, limit=None, hint="", *, visible=False):
    if formfield is None:
        return None
    if limit:
        formfield.max_length = limit
        widget_name = formfield.widget.__class__.__name__.lower()
        use_visible = visible or "tinymce" in widget_name
        if hasattr(formfield.widget, "attrs"):
            formfield.widget.attrs["maxlength"] = str(limit)
            if use_visible:
                formfield.widget.attrs["data-gestia-visible-count"] = "1"
        formfield.validators = [
            item for item in formfield.validators if not isinstance(item, MaxLengthValidator)
        ]
        formfield.validators = [
            item
            for item in formfield.validators
            if getattr(item, "__name__", "")[:19] != "visible_max_length_"
        ]
        if use_visible:
            formfield.validators.append(visible_max_length(limit))
        else:
            formfield.validators.append(MaxLengthValidator(limit))
    if hint:
        formfield.help_text = hint
    return formfield
