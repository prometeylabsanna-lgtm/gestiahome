"""Allowlist для форматованого тексту. style і скрипти прибираються."""

from __future__ import annotations

import re
from html import unescape

import nh3
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

ALLOWED_TAGS = frozenset(
    {
        "p",
        "br",
        "strong",
        "em",
        "u",
        "a",
        "ul",
        "ol",
        "li",
        "h2",
        "h3",
        "h4",
        "blockquote",
        "span",
    }
)
ALLOWED_ATTRIBUTES = {"a": frozenset({"href", "target"})}
URL_SCHEMES = frozenset({"http", "https", "mailto"})
_OUTER_P = re.compile(r"(?is)^\s*<p(?:\s[^>]*)?>(.*)</p>\s*$")
_BLOCK_BREAK = re.compile(r"(?i)</p>\s*<p(?:\s[^>]*)?>|<br\s*/?>|</?(?:ul|ol|li|h[2-4]|blockquote)\b")


def _attribute_value(tag: str, attribute: str, value: str) -> str | None:
    if tag == "a" and attribute == "target":
        return "_blank" if value == "_blank" else None
    return value


def sanitize_rich_html(value: str | None) -> str:
    text = value or ""
    if not text.strip():
        return ""
    cleaned = nh3.clean(
        text,
        tags=set(ALLOWED_TAGS),
        attributes={tag: set(names) for tag, names in ALLOWED_ATTRIBUTES.items()},
        attribute_filter=_attribute_value,
        url_schemes=set(URL_SCHEMES),
        link_rel="noopener noreferrer",
        strip_comments=True,
        generic_attribute_prefixes=set(),
    )
    return cleaned.strip()


def visible_text(value: str | None) -> str:
    """Visible characters only (tags stripped, entities decoded)."""
    raw = unescape(strip_tags(value or "")).replace("\xa0", " ")
    return raw


def visible_text_length(value: str | None) -> int:
    return len(visible_text(value))


def strip_outer_p(value: str | None) -> str:
    """Remove a single wrapping <p>…</p> when there are no nested block breaks."""
    text = (value or "").strip()
    if not text:
        return ""
    match = _OUTER_P.match(text)
    if not match:
        return text
    inner = match.group(1)
    if _BLOCK_BREAK.search(inner):
        return text
    return inner.strip()


def visible_max_length(limit: int):
    """Validator: count visible characters, not raw HTML length."""

    def _validator(value):
        if value in (None, ""):
            return
        if visible_text_length(str(value)) > limit:
            raise ValidationError(
                f"Не більше {limit} символів тексту (без урахування розмітки).",
                code="max_length",
            )

    _validator.__name__ = f"visible_max_length_{limit}"
    return _validator
