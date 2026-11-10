from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.content.models_thankyou import ThankYouPage
from src.content.literals import LITERALS


class ThanksNdTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.page = ThankYouPage.load()
        self.page.order_title_uk = "Раді стати частиною ваших традицій!"
        self.page.order_title_en = "We’re happy to be part of your traditions!"
        self.page.order_text_uk = (
            "<p>Замовлення № {number} оформлено. Після відправлення ви отримаєте "
            "номер накладної для відстеження.</p>"
        )
        self.page.order_text_en = (
            "<p>Your order No. {number} has been placed. Once it ships, we’ll "
            "send you a tracking number.</p>"
        )
        self.page.order_text_nonum_uk = (
            "<p>Замовлення оформлено. Після відправлення ви отримаєте номер "
            "накладної для відстеження.</p>"
        )
        self.page.order_text_nonum_en = (
            "<p>Your order has been placed. Once it ships, we’ll send you a "
            "tracking number.</p>"
        )
        self.page.link_uk = "На головну"
        self.page.link_en = "Back to home"
        self.page.contact_title_uk = "Дякуємо"
        self.page.contact_title_en = "Thank you"
        self.page.contact_text_uk = (
            "<p>Ми отримали ваше повідомлення і незабаром відповімо.</p>"
        )
        self.page.contact_text_en = (
            "<p>We’ve received your message and will get back to you soon.</p>"
        )
        self.page.save()

    def _session_number(self, number):
        session = self.client.session
        session["orders_done"] = [number]
        session.save()

    def test_order_with_number_from_cms(self):
        self._session_number("G-100")
        response = self.client.get("/thank-you/?kind=order&number=G-100")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Раді стати частиною ваших традицій!")
        self.assertContains(response, "G-100")
        self.assertContains(response, 'data-qa="order-number"')
        self.assertContains(response, "На головну")
        self.assertContains(response, "css/nd/thanks.css")
        self.assertNotContains(response, "css/pages/utility.css")
        self.assertContains(response, 'data-qa="thanks-page"')
        self.assertContains(response, 'data-qa="lead-success"')

    def test_number_is_escaped(self):
        evil = "<script>alert(1)</script>"
        self._session_number(evil)
        response = self.client.get(
            "/thank-you/",
            {"kind": "order", "number": evil},
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertContains(response, 'data-qa="order-number"')

    def test_foreign_number_hidden(self):
        response = self.client.get("/thank-you/?kind=order&number=GS-FOREIGN")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Раді стати частиною ваших традицій!")
        self.assertContains(
            response,
            "Замовлення оформлено. Після відправлення ви отримаєте номер",
        )
        self.assertNotContains(response, 'data-qa="order-number"')
        main = response.content.decode().split('<main id="main">', 1)[-1].split("</main>", 1)[0]
        self.assertNotIn("GS-FOREIGN", main)

    def test_without_number_uses_nonum(self):
        response = self.client.get("/thank-you/?kind=order")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Замовлення оформлено. Після відправлення ви отримаєте номер",
        )
        self.assertNotContains(response, 'data-qa="order-number"')

    def test_contact_kind(self):
        response = self.client.get("/thank-you/?kind=contact")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Дякуємо")
        self.assertContains(response, "Ми отримали ваше повідомлення")
        self.assertContains(response, 'data-qa="lead-success"')

    def test_english_texts(self):
        self._session_number("G-EN")
        response = self.client.get("/en/thank-you/?kind=order&number=G-EN")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We’re happy to be part of your traditions!")
        self.assertContains(response, "Your order No.")
        self.assertContains(response, "G-EN")
        self.assertContains(response, "Back to home")

        contact = self.client.get("/en/thank-you/?kind=contact")
        self.assertContains(contact, "Thank you")
        self.assertContains(contact, "We’ve received your message")

    def test_cms_field_change_updates_render(self):
        self.page.order_title_uk = "Новий заголовок подяки"
        self.page.save(update_fields=["order_title_uk"])
        cache.clear()
        response = self.client.get("/thank-you/?kind=order")
        self.assertContains(response, "Новий заголовок подяки")


class ThanksAdminTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_superuser(
            username="thanks-admin",
            email="thanks-admin@example.com",
            password="pass",
        )
        self.client.force_login(self.user)
        ThankYouPage.load()

    def test_admin_change_opens(self):
        for name in (
            "admin:content_thankyouorder_changelist",
            "admin:content_thankyoucontact_changelist",
        ):
            response = self.client.get(reverse(name), follow=True)
            self.assertEqual(response.status_code, 200, name)


def _seed_about_faq_en():
    import importlib

    from django.apps import apps

    module = importlib.import_module("src.content.migrations.0043_seed_about_faq_en")
    module.seed_forward(apps, None)


class AboutFaqEnSeedTests(TestCase):
    def test_migration_does_not_overwrite_nonempty_en(self):
        from src.content.models import AboutPage
        from src.content.models_faq import FaqItem, FaqPage

        cache.clear()
        about = AboutPage.load()
        about.intro_text_en = "<p>Keep my custom intro</p>"
        about.save(update_fields=["intro_text_en"])

        faq = FaqPage.load()
        item = FaqItem.objects.filter(
            page=faq, question_uk="Що входить у святковий бокс?"
        ).first()
        self.assertIsNotNone(item)
        item.answer_en = "<p>Custom answer stays</p>"
        item.save(update_fields=["answer_en"])

        _seed_about_faq_en()

        about.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(about.intro_text_en, "<p>Keep my custom intro</p>")
        self.assertEqual(item.answer_en, "<p>Custom answer stays</p>")

    def test_en_pages_show_seeded_copy(self):
        from src.content.models import FooterLink

        cache.clear()
        _seed_about_faq_en()
        cache.clear()

        FooterLink.objects.get_or_create(
            column="info",
            url_name="faq",
            defaults={
                "label_uk": "Актуальні питання",
                "label_en": "FAQ",
                "sort": 4,
            },
        )

        about_page = self.client.get("/en/pro-nas/")
        self.assertEqual(about_page.status_code, 200)
        self.assertContains(about_page, "the woman who creates a home")

        faq_page = self.client.get("/en/aktualni-pytannia/")
        self.assertEqual(faq_page.status_code, 200)
        self.assertContains(faq_page, "Still have questions?")
        self.assertContains(faq_page, "What’s inside a festive box?")

        self.assertEqual(LITERALS["nav_faq"][1], "FAQ")
