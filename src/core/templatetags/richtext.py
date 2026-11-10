import re

from django import template
from django.utils.html import escape, linebreaks
from django.utils.safestring import mark_safe

from src.core.html_sanitize import sanitize_rich_html, strip_outer_p

register = template.Library()

_BLOCK_SPLIT = re.compile(r"(?i)</p>\s*<p[^>]*>|<br\s*/?>")
_STRIP_P = re.compile(r"(?i)</?p[^>]*>")
_HAS_LIST = re.compile(r"(?i)<(?:ul|ol)\b")


def _looks_like_html(text: str) -> bool:
    return "<" in text and ">" in text


def _split_line_items(cleaned: str) -> list[str] | None:
    """Split CMS text into spaced items. None = keep list markup as-is."""
    if _HAS_LIST.search(cleaned):
        return None
    if not _looks_like_html(cleaned):
        return [part.strip() for part in re.split(r"\n+", cleaned) if part.strip()]
    parts = []
    for chunk in _BLOCK_SPLIT.split(cleaned):
        item = _STRIP_P.sub("", chunk).strip()
        if item:
            parts.append(item)
    return parts


@register.filter(name="richhtml")
def richhtml(value):
    text = value if isinstance(value, str) else ""
    cleaned = sanitize_rich_html(text)
    if not cleaned:
        return ""
    if not _looks_like_html(cleaned):
        return mark_safe(linebreaks(cleaned))
    return mark_safe(cleaned)


@register.filter(name="richlines")
def richlines(value):
    """CMS text as spaced block items (p/li/newlines/br) for delivery/payment lists."""
    text = value if isinstance(value, str) else ""
    cleaned = sanitize_rich_html(text)
    if not cleaned:
        return ""
    parts = _split_line_items(cleaned)
    if parts is None:
        return mark_safe(cleaned)
    if not parts:
        return ""
    return mark_safe("".join(f"<p>{part}</p>" for part in parts))


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


@register.filter(name="richhtml_number")
def richhtml_number(value, number):
    """Sanitize CMS HTML and safely substitute {number} (escaped, data-qa span)."""
    text = value if isinstance(value, str) else ""
    cleaned = sanitize_rich_html(text)
    if not cleaned:
        return ""
    raw = "" if number is None else str(number)
    if raw:
        safe = escape(raw)
        replacement = f'<span data-qa="order-number">{safe}</span>'
    else:
        replacement = ""
    if not _looks_like_html(cleaned):
        cleaned = str(linebreaks(cleaned))
    return mark_safe(cleaned.replace("{number}", replacement))
