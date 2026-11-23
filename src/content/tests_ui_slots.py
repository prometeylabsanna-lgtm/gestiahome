from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.content.models import SiteSettings
from src.content.models_contacts import ContactsPage
from src.content.models_ui import InterfaceCopy
from src.content.ui_text import text


class LoginCopyTests(TestCase):
    def test_login_screen_is_ukrainian(self):
        page = self.client.get(reverse("admin:login"))
        self.assertContains(page, "З поверненням до")
        self.assertContains(page, "Увійти")
        self.assertNotContains(page, "Welcome back to")


class CharCounterTests(TestCase):
    def test_username_field_is_skipped(self):
        source = Path(find("js/admin/char_counter.js")).read_text()
        self.assertIn('=== "username"', source)
        self.assertIn("max <= 160", source)


class InterfaceFallbackTests(TestCase):
    def test_empty_ukrainian_stays_empty_and_empty_english_uses_ukrainian(self):
        copy = InterfaceCopy.load()
        copy.cart_uk = ""
        copy.cart_en = "Basket"
        copy.save()
        translation.activate("uk")
        self.assertEqual(text("cart"), "")
        copy.cart_uk = "Кошик"
        copy.cart_en = ""
        copy.save()
        translation.activate("en")
        self.assertEqual(text("cart"), "Кошик")
        copy.cart_en = "Basket"
        copy.cart_fr = ""
        copy.save()
        translation.activate("fr")
        self.assertEqual(text("cart"), "Кошик")

    def test_cms_tag_does_not_read_literals(self):
        from django.template import Context, Template

        html = Template('{% load content_tags %}{% cms "" "nav_about" %}').render(Context())
        self.assertEqual(html, "")


class MarkAndContactsTests(TestCase):
    def test_footer_mark_comes_from_site_settings(self):
        page = self.client.get(reverse("home"))
        self.assertContains(page, "site/g-mark-dark.png")
        self.assertNotContains(page, "nd/g-mark-dark.png")
        site = SiteSettings.load()
        site.mark_dark = None
        site.save()
        cleared = self.client.get(reverse("home"))
        self.assertNotContains(cleared, 'class="nd-footer__g"')

    def test_contacts_title_comes_from_the_page(self):
        page = ContactsPage.load()
        page.title_uk = "Майстерня"
        page.seo_title_uk = "Майстерня Gestia"
        page.save()
        response = self.client.get(reverse("contacts"))
        self.assertContains(response, "Майстерня")
        self.assertContains(response, "<title>Майстерня Gestia")
        self.assertNotContains(response, "Контакти Gestia Home — телефон")

    def test_seeded_mark_file_exists(self):
        site = SiteSettings.load()
        self.assertTrue(site.mark_light)
        self.assertTrue((Path(settings.MEDIA_ROOT) / site.mark_light.name).is_file())
