import re
import secrets

from django import forms
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from src.commerce.models import Order
from src.commerce.validators import (
    EMAIL_ERRORS,
    MSG_REQUIRED,
    NAME_ERRORS,
    NAME_PATTERN,
    PHONE_ERRORS,
    PHONE_PATTERN,
    apply_ui_messages,
    clean_name_value,
    clean_phone_value,
)


class ConsentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_ui_messages(self)

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
    message = forms.CharField(
        label=_("Повідомлення"),
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def clean_message(self):
        raw = self.cleaned_data.get("message") or ""
        text = strip_tags(raw)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()


class CallbackForm(NamePhoneMixin, ConsentForm):
    name = forms.CharField(label=_("Ім'я"), max_length=120, error_messages=NAME_ERRORS.copy())
    phone = forms.CharField(label=_("Телефон"), max_length=32, error_messages=PHONE_ERRORS.copy())
    sku = forms.CharField(max_length=64, widget=forms.HiddenInput)


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


class CheckoutForm(NamePhoneMixin, ConsentForm):
    name = forms.CharField(label=_("Ім’я"), max_length=120, error_messages=NAME_ERRORS.copy())
    phone = forms.CharField(label=_("Номер телефону"), max_length=32, error_messages=PHONE_ERRORS.copy())
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        error_messages=EMAIL_ERRORS.copy(),
    )
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
    city_ref = forms.CharField(required=False, max_length=64, widget=forms.HiddenInput)
    warehouse_ref = forms.CharField(required=False, max_length=64, widget=forms.HiddenInput)
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

    def __init__(self, *args, card_enabled=False, **kwargs):
        super().__init__(*args, **kwargs)
        on_delivery = (Order.Payment.ON_DELIVERY, _("При отриманні (інший погоджений спосіб)"))
        if card_enabled:
            self.fields["payment_method"].choices = [
                (Order.Payment.CARD, _("Онлайн карткою на сайті")),
                on_delivery,
            ]
            if not self.is_bound:
                self.fields["payment_method"].initial = Order.Payment.CARD
        else:
            self.fields["payment_method"].choices = [on_delivery]
            if not self.is_bound:
                self.fields["payment_method"].initial = Order.Payment.ON_DELIVERY
        self._apply_choice_labels()

    def _apply_choice_labels(self):
        from src.content.ui_text import text_or_default

        labels = {
            Order.Delivery.BRANCH: text_or_default("ship_branch"),
            Order.Delivery.LOCKER: text_or_default("ship_locker"),
            Order.Delivery.COURIER: text_or_default("ship_courier"),
            Order.Payment.CARD: text_or_default("pay_card"),
            Order.Payment.ON_DELIVERY: text_or_default("pay_delivery"),
        }
        for name in ("delivery_method", "payment_method"):
            self.fields[name].choices = [
                (value, labels[value])
                for value, _label in self.fields[name].choices
            ]

    def clean(self):
        cleaned = super().clean()
        address = (cleaned.get("address") or "").strip()
        method = cleaned.get("delivery_method")
        city = (cleaned.get("city") or "").strip()
        branch = (cleaned.get("branch") or "").strip()
        house = (cleaned.get("house") or "").strip()
        apartment = (cleaned.get("apartment") or "").strip()
        city_ref = (cleaned.get("city_ref") or "").strip()[:64]
        warehouse_ref = (cleaned.get("warehouse_ref") or "").strip()[:64]
        if method == Order.Delivery.COURIER:
            warehouse_ref = ""
        elif warehouse_ref:
            from src.commerce.np_catalog import resolve_warehouse

            kind = "locker" if method == Order.Delivery.LOCKER else "branch"
            found = resolve_warehouse(warehouse_ref, kind=kind, city_ref=city_ref)
            if found is None:
                from src.content.ui_text import text_or_default

                self.add_error("branch", text_or_default("checkout_pick_branch"))
            else:
                warehouse_ref = found["ref"]
                city_ref = found["city_ref"]
                branch = found["label"][:255]
                if found["city_name"]:
                    city = found["city_name"][:120]
        if not address:
            if method == Order.Delivery.COURIER:
                from src.content.ui_text import text_or_default

                parts = [city, branch]
                if house:
                    parts.append(f"{text_or_default('house_ph')} {house}")
                if apartment:
                    parts.append(f"{text_or_default('apt_ph')} {apartment}")
                address = ", ".join(part for part in parts if part)
            else:
                address = ", ".join(part for part in (city, branch) if part)
        elif method == Order.Delivery.COURIER:
            from src.content.ui_text import text_or_default

            house_label = text_or_default("house_ph")
            apt_label = text_or_default("apt_ph")
            extras = []
            if house and f"{house_label} {house}" not in address:
                extras.append(f"{house_label} {house}")
            if apartment and f"{apt_label} {apartment}" not in address:
                extras.append(f"{apt_label} {apartment}")
            if extras:
                address = f"{address}, {', '.join(extras)}"
        if not address:
            from src.content.ui_text import text

            self.add_error("city", text("msg_required"))
        cleaned["city"] = city
        cleaned["branch"] = branch
        cleaned["city_ref"] = city_ref
        cleaned["warehouse_ref"] = warehouse_ref
        cleaned["address"] = address[:255]
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
                    "maxlength": "120",
                    "pattern": NAME_PATTERN,
                }
            )
        if name == "email":
            field.widget.attrs["autocomplete"] = "email"
        if name == "message":
            field.widget.attrs["maxlength"] = "2000"
        if name in {"address"}:
            field.widget.attrs["autocomplete"] = "street-address"
    return form
