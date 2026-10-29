import secrets

from django import forms
from django.utils.translation import gettext_lazy as _

from src.commerce.models import Order
from src.commerce.validators import (
    EMAIL_ERRORS,
    MSG_REQUIRED,
    NAME_ERRORS,
    NAME_PATTERN,
    PHONE_ERRORS,
    PHONE_PATTERN,
    clean_name_value,
    clean_phone_value,
)


class ConsentForm(forms.Form):
    consent = forms.BooleanField(
        label=_("Погоджуюсь на обробку персональних даних"),
        required=True,
        error_messages={"required": MSG_REQUIRED},
    )


class NamePhoneMixin:
    def clean_name(self):
        return clean_name_value(self.cleaned_data["name"])

    def clean_phone(self):
        return clean_phone_value(self.cleaned_data["phone"])


class ContactForm(NamePhoneMixin, ConsentForm):
    name = forms.CharField(label=_("Ім'я"), max_length=120, error_messages=NAME_ERRORS.copy())
    phone = forms.CharField(label=_("Телефон"), max_length=32, error_messages=PHONE_ERRORS.copy())
    message = forms.CharField(label=_("Повідомлення"), required=False, widget=forms.Textarea(attrs={"rows": 4}))


class CallbackForm(NamePhoneMixin, ConsentForm):
    name = forms.CharField(label=_("Ім'я"), max_length=120, error_messages=NAME_ERRORS.copy())
    phone = forms.CharField(label=_("Телефон"), max_length=32, error_messages=PHONE_ERRORS.copy())
    sku = forms.CharField(widget=forms.HiddenInput)


class BuyNowForm(NamePhoneMixin, ConsentForm):
    name = forms.CharField(label=_("Ім'я"), max_length=120, error_messages=NAME_ERRORS.copy())
    phone = forms.CharField(label=_("Телефон"), max_length=32, error_messages=PHONE_ERRORS.copy())
    address = forms.CharField(
        label=_("Адреса доставки"),
        max_length=255,
        error_messages={"required": MSG_REQUIRED},
    )
    sku = forms.CharField(widget=forms.HiddenInput)
    idem = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["idem"].initial = secrets.token_urlsafe(16)


class WaitlistForm(ConsentForm):
    email = forms.EmailField(label=_("Email"), max_length=254, error_messages=EMAIL_ERRORS.copy())


class CheckoutForm(NamePhoneMixin, ConsentForm):
    name = forms.CharField(label=_("Ім’я"), max_length=120, error_messages=NAME_ERRORS.copy())
    phone = forms.CharField(label=_("Номер телефону"), max_length=32, error_messages=PHONE_ERRORS.copy())
    email = forms.EmailField(label=_("Email"), error_messages=EMAIL_ERRORS.copy())
    delivery_method = forms.ChoiceField(
        label=_("Доставка"),
        choices=[
            (Order.Delivery.BRANCH, _("Нова пошта (відділення)")),
            (Order.Delivery.LOCKER, _("Нова пошта (поштамат)")),
            (Order.Delivery.COURIER, _("Кур’єрська доставка")),
        ],
        initial=Order.Delivery.BRANCH,
    )
    city = forms.CharField(label=_("Місто"), max_length=120, required=False)
    branch = forms.CharField(label=_("Відділення"), max_length=255, required=False)
    house = forms.CharField(label=_("Будинок"), max_length=24, required=False)
    apartment = forms.CharField(label=_("Квартира"), max_length=16, required=False)
    address = forms.CharField(label=_("Адреса доставки"), max_length=255, required=False)
    payment_method = forms.ChoiceField(
        label=_("Оплата"),
        choices=[
            (Order.Payment.CARD, _("Онлайн карткою на сайті")),
            (Order.Payment.ON_DELIVERY, _("При отриманні (інший погоджений спосіб)")),
        ],
        initial=Order.Payment.ON_DELIVERY,
    )

    def clean(self):
        cleaned = super().clean()
        address = (cleaned.get("address") or "").strip()
        method = cleaned.get("delivery_method")
        city = (cleaned.get("city") or "").strip()
        branch = (cleaned.get("branch") or "").strip()
        house = (cleaned.get("house") or "").strip()
        apartment = (cleaned.get("apartment") or "").strip()
        if not address:
            if method == Order.Delivery.COURIER:
                parts = [city, branch]
                if house:
                    parts.append(f"буд. {house}")
                if apartment:
                    parts.append(f"кв. {apartment}")
                address = ", ".join(part for part in parts if part)
            else:
                address = ", ".join(part for part in (city, branch) if part)
        elif method == Order.Delivery.COURIER:
            extras = []
            if house and f"буд. {house}" not in address:
                extras.append(f"буд. {house}")
            if apartment and f"кв. {apartment}" not in address:
                extras.append(f"кв. {apartment}")
            if extras:
                address = f"{address}, {', '.join(extras)}"
        if not address:
            self.add_error("city", MSG_REQUIRED)
        cleaned["address"] = address
        return cleaned


def style_form(form):
    validate = {
        "name": "name",
        "phone": "phone",
        "email": "email",
        "address": "required",
        "consent": "consent",
    }
    for name, field in form.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "field__check"
        elif isinstance(field.widget, forms.Textarea):
            field.widget.attrs["class"] = "field__input field__input--area"
        elif not isinstance(field.widget, forms.HiddenInput):
            field.widget.attrs["class"] = "field__input"
        if name in validate:
            field.widget.attrs["data-validate"] = validate[name]
        if name == "phone":
            field.widget.attrs.update(
                {
                    "inputmode": "tel",
                    "autocomplete": "tel",
                    "maxlength": "19",
                    "pattern": PHONE_PATTERN,
                }
            )
        if name == "name":
            field.widget.attrs.update(
                {
                    "autocomplete": "name",
                    "autocapitalize": "words",
                    "spellcheck": "false",
                    "pattern": NAME_PATTERN,
                }
            )
        if name == "email":
            field.widget.attrs["autocomplete"] = "email"
        if name in {"address"}:
            field.widget.attrs["autocomplete"] = "street-address"
    return form
