import re

from django.core.exceptions import ValidationError

TOKEN_INK = "#241c16"
TOKEN_PAPER = "#f3eee6"
TOKEN_ACCENT = "#8d3b2a"
TOKEN_CHROME = "#ffffff"

_HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")
_HEX3 = re.compile(r"^#[0-9a-fA-F]{3}$")


def normalize_hex(value: str | None) -> str:
    raw = (value or "").strip()
    if _HEX3.match(raw):
        raw = "#" + "".join(ch * 2 for ch in raw[1:])
    if _HEX6.match(raw):
        return raw.lower()
    return ""


def validate_hex_color(value: str) -> None:
    if not normalize_hex(value):
        raise ValidationError("Вкажіть колір у форматі #241c16.")
