from django import template
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe

from src.core.html_sanitize import sanitize_rich_html, strip_outer_p

register = template.Library()


def _looks_like_html(text: str) -> bool:
    return "<" in text and ">" in text


@register.filter(name="richhtml")
def richhtml(value):
    text = value if isinstance(value, str) else ""
    cleaned = sanitize_rich_html(text)
    if not cleaned:
        return ""
    if not _looks_like_html(cleaned):
        return mark_safe(linebreaks(cleaned))
    return mark_safe(cleaned)


@register.filter(name="richinline")
def richinline(value):
    """Sanitize and unwrap a single outer <p> for use inside inline containers."""
    text = value if isinstance(value, str) else ""
    cleaned = sanitize_rich_html(text)
    if not cleaned:
        return ""
    if not _looks_like_html(cleaned):
        return mark_safe(cleaned.replace("\n", "<br>"))
    return mark_safe(strip_outer_p(cleaned))
