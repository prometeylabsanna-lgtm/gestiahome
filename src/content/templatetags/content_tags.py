from django import template

from src.core.utils import localized

register = template.Library()


def _filled(value):
    return isinstance(value, str) and bool(value.strip())


@register.simple_tag
def cms(value, key=""):
    del key
    if _filled(value):
        return value
    return ""


@register.simple_tag
def cms_field(obj, field):
    value = ""
    if obj is not None and hasattr(obj, f"{field}_uk"):
        value = localized(obj, field)
    if _filled(value):
        return value
    return ""
