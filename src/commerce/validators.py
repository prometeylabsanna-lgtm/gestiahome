import re

from django import forms
from django.utils.translation import gettext_lazy as _

UA_MOBILE_CODES = (
    "39",
    "50",
    "63",
    "66",
    "67",
    "68",
    "73",
    "77",
    "91",
    "92",
    "93",
    "94",
    "95",
    "96",
    "97",
    "98",
    "99",
)

_NAME_LETTERS = "A-Za-zА-Яа-яЁёІіЇїЄєҐґ"
_NAME_SEPARATORS = "'\u2019\u02bc -"
NAME_PATTERN = rf"[{_NAME_LETTERS}]+(?:[{_NAME_SEPARATORS}][{_NAME_LETTERS}]+)*"
NAME_ALLOWED_RE = re.compile(NAME_PATTERN)
NAME_LETTER_RE = re.compile(rf"[{_NAME_LETTERS}]")
PHONE_PATTERN = rf"\+38 \(0(?:{'|'.join(UA_MOBILE_CODES)})\) \d{{3}}-\d{{2}}-\d{{2}}"
PHONE_LETTER_RE = re.compile(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ]")

def _ui(key):
    from src.content.ui_text import text

    return text(key)


def _required():
    return _ui("msg_required")


def _name_msg():
    return _ui("msg_name")


def _name_short():
    return _ui("msg_name_short")


def _phone_msg():
    return _ui("msg_phone")


def _email_msg():
    return _ui("msg_email")


MSG_REQUIRED = _("Поле обов'язкове для заповнення")
MSG_NAME = _(
    "Ім'я не може містити цифри або спецсимволи. Будь ласка, використовуйте лише букви"
)
MSG_NAME_SHORT = _("Занадто коротке значення")
MSG_PHONE = _("Введіть коректний номер мобільного телефону у форматі +380 (XX) XXX-XX-XX")
MSG_EMAIL = _("Некоректний формат")

NAME_ERRORS = {"required": MSG_REQUIRED}
PHONE_ERRORS = {"required": MSG_REQUIRED}
EMAIL_ERRORS = {"required": MSG_REQUIRED, "invalid": MSG_EMAIL}


def apply_ui_messages(form):
    required = _required()
    email = _email_msg()
    for field in form.fields.values():
        if required and "required" in field.error_messages:
            field.error_messages["required"] = required
        if email and getattr(field, "error_messages", None) and "invalid" in field.error_messages:
            if field.__class__.__name__ == "EmailField":
                field.error_messages["invalid"] = email
    return form


def clean_name_value(name: str) -> str:
    name = re.sub(r"\s+", " ", (name or "").strip())
    if not name:
        raise forms.ValidationError(_required())
    if not NAME_ALLOWED_RE.fullmatch(name):
        raise forms.ValidationError(_name_msg())
    if len(NAME_LETTER_RE.findall(name)) < 2:
        raise forms.ValidationError(_name_short())
    return name


def clean_phone_value(phone: str) -> str:
    phone = (phone or "").strip()
    if not phone:
        raise forms.ValidationError(_required())
    if PHONE_LETTER_RE.search(phone):
        raise forms.ValidationError(_phone_msg())
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("380") and len(digits) == 12:
        normalized = f"+{digits}"
    elif digits.startswith("0") and len(digits) == 10:
        normalized = f"+38{digits}"
    elif len(digits) == 9:
        normalized = f"+380{digits}"
    else:
        raise forms.ValidationError(_phone_msg())
    if normalized[4:6] not in UA_MOBILE_CODES:
        raise forms.ValidationError(_phone_msg())
    return normalized
