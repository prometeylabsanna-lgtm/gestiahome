from decimal import Decimal
from unittest.mock import patch

from django import forms
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Product
from src.commerce.cart_panel import panel_context
from src.commerce.forms import CheckoutForm
from src.commerce.models import Order
from src.commerce.notify import notify_order
from src.commerce.services import unavailable_message
from src.content.models_thankyou import EMAIL_BODY_DEFAULTS, EMAIL_SUBJECT_DEFAULTS, ThankYouPage
from src.content.models_ui import InterfaceCopy
from src.content.ui_defaults import UI_FIELDS
from src.content.ui_fr import UI_FR
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

    def test_checkout_clear_comes_from_interface_copy(self):
        cache.clear()
        copy = InterfaceCopy.load()
        copy.clear_uk = "Прибрати поле"
        copy.save()
        category = Category.objects.create(slug="clr-cat", name_uk="Каталог")
        Product.objects.create(
            category=category,
            sku="CLR-1",
            slug="clr-1",
            name_uk="Бокс",
            price_uah=Decimal("100"),
            price_eur=Decimal("3"),
            stock_qty=5,
        )
        session = self.client.session
        session["cart"] = {"CLR-1": 1}
        session["currency"] = "uah"
        session.save()
        with translation.override("uk"):
            response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-np-clear')
        self.assertContains(response, 'aria-label="Прибрати поле"')

    def test_courier_address_uses_key_defaults_when_empty(self):
        cache.clear()
        copy = InterfaceCopy.load()
        for lang in ("uk", "en", "fr"):
            setattr(copy, f"house_ph_{lang}", "")
            setattr(copy, f"apt_ph_{lang}", "")
        copy.save()
        base = {
            "name": "Оля",
            "phone": "+380671112233",
            "email": "olya@example.com",
            "delivery_method": Order.Delivery.COURIER,
            "city": "Lyon",
            "branch": "Rue",
            "house": "10",
            "apartment": "4",
            "payment_method": Order.Payment.ON_DELIVERY,
            "consent": "on",
        }
        house = UI_FR["house_ph"]
        apt = UI_FR["apt_ph"]
        with translation.override("fr"):
            built = CheckoutForm(base, card_enabled=False)
            self.assertTrue(built.is_valid(), built.errors)
            given = CheckoutForm({**base, "address": "Lyon, Rue"}, card_enabled=False)
            self.assertTrue(given.is_valid(), given.errors)
        self.assertEqual(built.cleaned_data["address"], f"Lyon, Rue, {house} 10, {apt} 4")
        self.assertEqual(given.cleaned_data["address"], f"Lyon, Rue, {house} 10, {apt} 4")
        self.assertNotIn("буд.", built.cleaned_data["address"])
        self.assertNotIn("кв.", given.cleaned_data["address"])

    def test_choice_labels_and_cart_aria_come_from_interface_copy(self):
        cache.clear()
        copy = InterfaceCopy.load()
        copy.ship_branch_uk = "Відділення з адмінки"
        copy.ship_locker_uk = "Поштомат з адмінки"
        copy.ship_courier_uk = "Кур’єр з адмінки"
        copy.pay_card_uk = "Картка з адмінки"
        copy.pay_delivery_uk = "При отриманні з адмінки"
        copy.cart_uk = "Мій кошик"
        copy.save()
        with translation.override("uk"):
            form = CheckoutForm(card_enabled=True)
            request = RequestFactory().get("/koshik/panel/")
            request.session = {}
            aria = panel_context(request, "")["aria_cart"]
        delivery = dict(form.fields["delivery_method"].choices)
        payment = dict(form.fields["payment_method"].choices)
        self.assertEqual(delivery[Order.Delivery.BRANCH], "Відділення з адмінки")
        self.assertEqual(delivery[Order.Delivery.LOCKER], "Поштомат з адмінки")
        self.assertEqual(delivery[Order.Delivery.COURIER], "Кур’єр з адмінки")
        self.assertEqual(payment[Order.Payment.CARD], "Картка з адмінки")
        self.assertEqual(payment[Order.Payment.ON_DELIVERY], "При отриманні з адмінки")
        self.assertEqual(aria, "Мій кошик")
