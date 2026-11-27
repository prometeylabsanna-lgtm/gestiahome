from decimal import Decimal
from unittest.mock import patch

from django import forms
from django.test import TestCase, override_settings
from django.utils import translation

from src.commerce.models import Order
from src.commerce.notify import notify_order
from src.commerce.services import unavailable_message
from src.content.models_thankyou import EMAIL_BODY_DEFAULTS, EMAIL_SUBJECT_DEFAULTS, ThankYouPage
from src.content.models_ui import InterfaceCopy
from src.content.ui_defaults import UI_FIELDS
from src.core.ratelimit import reject_if_limited


def _order(**extra):
    data = {
        "number": "GS-COPY-1",
        "source": Order.Source.CART,
        "customer_name": "Олена",
        "phone": "+380501112233",
        "email": "client@example.com",
        "language": "uk",
        "currency": "uah",
        "delivery_method": Order.Delivery.BRANCH,
        "delivery_address": "Київ, 1",
        "payment_method": Order.Payment.ON_DELIVERY,
        "total": Decimal("10.00"),
        "consent": True,
    }
    data.update(extra)
    return Order.objects.create(**data)


@override_settings(ORDER_NOTIFY_EMAIL="")
class HardcodeCopyTests(TestCase):
    @patch("src.commerce.notify.send_telegram_message", return_value=False)
    @patch("src.commerce.notify.send_mail")
    def test_customer_email_uses_thank_you_page(self, send_mail, _telegram):
        page = ThankYouPage.load()
        page.email_subject_uk = "Тема {number}"
        page.email_body_uk = "Тіло 100% {number} {extra}"
        page.email_subject_en = "Sub {number}"
        page.email_body_en = "Body {number}"
        page.save()
        notify_order(_order(number="GS-UK", language="uk", email="uk@example.com").pk)
        notify_order(_order(number="GS-EN", language="en", email="en@example.com").pk)
        uk_call, en_call = send_mail.call_args_list
        self.assertEqual(uk_call.kwargs["subject"], "Тема GS-UK")
        self.assertEqual(uk_call.kwargs["message"], "Тіло 100% GS-UK {extra}")
        self.assertEqual(uk_call.kwargs["recipient_list"], ["uk@example.com"])
        self.assertEqual(en_call.kwargs["subject"], "Sub GS-EN")
        self.assertEqual(en_call.kwargs["message"], "Body GS-EN")
        self.assertEqual(en_call.kwargs["recipient_list"], ["en@example.com"])

    @patch("src.commerce.notify.send_telegram_message", return_value=False)
    @patch("src.commerce.notify.send_mail")
    def test_customer_email_falls_back_when_fields_empty(self, send_mail, _telegram):
        page = ThankYouPage.load()
        for lang in ("uk", "en", "fr"):
            setattr(page, f"email_subject_{lang}", "")
            setattr(page, f"email_body_{lang}", "")
        page.save()
        notify_order(_order(number="GS{extra}", language="uk").pk)
        call = send_mail.call_args
        self.assertEqual(call.kwargs["subject"], "Замовлення GS{extra}")
        self.assertEqual(
            call.kwargs["message"],
            EMAIL_BODY_DEFAULTS["uk"].replace("{number}", "GS{extra}"),
        )
        self.assertEqual(call.kwargs["subject"], EMAIL_SUBJECT_DEFAULTS["uk"].replace("{number}", "GS{extra}"))

    def test_unavailable_message_comes_from_interface_copy(self):
        copy = InterfaceCopy.load()
        copy.cart_item_unavailable_uk = "Немає «{name}» 100% {extra}"
        copy.save()
        with translation.override("uk"):
            self.assertEqual(
                unavailable_message("Ваза {left}"),
                "Немає «Ваза {left}» 100% {extra}",
            )

    def test_rate_limit_message_comes_from_interface_copy(self):
        copy = InterfaceCopy.load()
        copy.form_rate_limit_uk = "Стоп, зачекайте"
        copy.save()
        form = forms.Form({})
        with translation.override("uk"):
            with patch("src.core.ratelimit.is_rate_limited", return_value=True):
                limited = reject_if_limited(None, form, "contact")
        self.assertTrue(limited)
        self.assertIn("Стоп, зачекайте", form.non_field_errors())

    def test_data_migration_fills_only_empty_fields(self):
        import importlib

        from django.apps import apps

        from src.content.ui_fr import UI_FR

        migration = importlib.import_module("src.content.migrations.0066_hardcode_copy")

        defaults = {item[0]: item for item in UI_FIELDS}
        copy = InterfaceCopy.objects.get(pk=1)
        uk, en = defaults["cart_unavailable_removed"][2], defaults["cart_unavailable_removed"][3]
        self.assertEqual(copy.cart_unavailable_removed_uk, uk)
        self.assertEqual(copy.cart_unavailable_removed_en, en)
        self.assertEqual(copy.cart_unavailable_removed_fr, UI_FR["cart_unavailable_removed"])
        self.assertEqual(copy.form_rate_limit_uk, defaults["form_rate_limit"][2])
        page = ThankYouPage.objects.get(pk=1)
        self.assertEqual(page.email_subject_uk, EMAIL_SUBJECT_DEFAULTS["uk"])
        self.assertEqual(page.email_body_fr, EMAIL_BODY_DEFAULTS["fr"])

        copy.form_rate_limit_uk = "Своє"
        copy.checkout_pick_branch_en = ""
        copy.save()
        page.email_subject_uk = "Лише тема"
        page.email_body_fr = ""
        page.save()
        migration.fill_empty(apps, None)
        copy.refresh_from_db()
        page.refresh_from_db()
        self.assertEqual(copy.form_rate_limit_uk, "Своє")
        self.assertEqual(copy.checkout_pick_branch_en, defaults["checkout_pick_branch"][3])
        self.assertEqual(page.email_subject_uk, "Лише тема")
        self.assertEqual(page.email_body_fr, EMAIL_BODY_DEFAULTS["fr"])
