from html import unescape

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.html import strip_tags

from src.content.legal_copy import DOCS, get_legal, sections_to_html
from src.content.legal_copy_en import DOCS_EN
from src.content.legal_copy_fr import DOCS_FR
from src.content.models_legal import LegalPage
from src.core.html_sanitize import sanitize_rich_html


class LegalPageRenderTests(TestCase):
    def test_urls_and_seeded_copy_match_the_literal(self):
        translation.activate("uk")
        paths = {
            "offer": "/publichnyi-dogovir/",
            "privacy": "/polityka-konfidentsiynosti/",
            "cookies": "/polityka-cookies/",
            "shipping": "/dostavka-ta-oplata/",
        }
        self.assertEqual(LegalPage.objects.count(), 4)
        for key, path in paths.items():
            self.assertEqual(reverse(key), path)
            page = LegalPage.objects.get(key=key)
            literal = get_legal(key)
            english = DOCS_EN[key]()
            self.assertEqual(page.title_uk, literal["title"])
            self.assertEqual(page.title_en, english["title"])
            self.assertEqual(page.body_en, sections_to_html(english["sections"]))
            self.assertEqual(page.seo_title_en, english["seo_title"])
            self.assertEqual(page.seo_description_en, english["seo_description"])
            french = DOCS_FR[key]()
            self.assertEqual(page.title_fr, french["title"])
            self.assertEqual(page.body_fr, sections_to_html(french["sections"]))
            self.assertEqual(page.body_uk.count("<h2>"), page.body_en.count("<h2>"))
            self.assertEqual(page.body_uk.count("<h2>"), page.body_fr.count("<h2>"))
            self.assertEqual(page.body_uk.count("<p>"), page.body_en.count("<p>"))
            self.assertEqual(page.body_uk.count("<p>"), page.body_fr.count("<p>"))
            self.assertEqual(page.seo_title_uk, literal["seo_title"])
            self.assertEqual(page.updated_on.strftime("%d.%m.%Y"), literal["updated"])
            self.assertEqual(page.body_uk, sections_to_html(literal["sections"]))
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            visible = unescape(strip_tags(response.content.decode()))
            self.assertIn(literal["title"], visible)
            self.assertIn(literal["updated"], response.content.decode())
            for section in literal["sections"]:
                self.assertIn(section["heading"], visible)
                for paragraph in section["paragraphs"]:
                    self.assertIn(paragraph, visible)
            self.assertContains(response, 'class="legal-copy"')
            copy = response.content.decode().split('class="legal-copy"', 1)[1].split("</div>", 1)[0]
            self.assertNotIn("<script", copy)
            self.assertNotIn("onerror", copy)
        for key, path in paths.items():
            english = DOCS_EN[key]()
            english_page = self.client.get(f"/en{path}")
            self.assertEqual(english_page.status_code, 200)
            main = english_page.content.decode().split('<main id="main">', 1)[1].split("</main>", 1)[0]
            self.assertNotRegex(main, r"[\u0400-\u04FF]")
            self.assertIn(english["title"], main)
            self.assertIn(english["sections"][0]["heading"], main)
            french = DOCS_FR[key]()
            french_page = self.client.get(f"/fr{path}")
            self.assertEqual(french_page.status_code, 200)
            french_main = french_page.content.decode().split('<main id="main">', 1)[1].split("</main>", 1)[0]
            self.assertNotRegex(french_main, r"[\u0400-\u04FF]")
            self.assertIn(french["title"], french_main)
            self.assertIn(french["sections"][0]["heading"], french_main)

    def test_empty_model_falls_back_to_the_literal(self):
        translation.activate("uk")
        LegalPage.objects.filter(key="privacy").update(title_uk="", body_uk="", seo_title_uk="", updated_on=None)
        response = self.client.get("/polityka-konfidentsiynosti/")
        literal = get_legal("privacy")
        self.assertContains(response, literal["title"])
        self.assertContains(response, literal["sections"][0]["heading"])
        self.assertContains(response, 'class="legal-sec"')
        self.assertContains(response, literal["seo_title"])

    def test_english_uses_translation_or_ukrainian_text(self):
        translation.activate("en")
        page = LegalPage.objects.get(key="shipping")
        page.title_en = ""
        page.body_en = ""
        page.save(update_fields=["title_en", "body_en"])
        ukrainian = self.client.get("/en/dostavka-ta-oplata/")
        self.assertContains(ukrainian, page.title_uk)
        self.assertContains(ukrainian, "Updated")
        page.title_en = "Delivery and payment"
        page.body_en = "<h2>Shipping</h2><p>Courier.</p><script>alert(1)</script>"
        page.save()
        english = self.client.get("/en/dostavka-ta-oplata/")
        self.assertContains(english, "Delivery and payment")
        self.assertContains(english, "Courier.")
        copy = english.content.decode().split('class="legal-copy"', 1)[1].split("</div>", 1)[0]
        self.assertNotIn("<script", copy)
        self.assertNotIn(page.title_uk, copy)
        stored = LegalPage.objects.get(key="shipping")
        self.assertNotIn("script", stored.body_en)

    def test_admin_opens_one_record_per_page(self):
        user = User.objects.create_superuser("legal", "legal@example.com", "pass-word-9")
        self.client.force_login(user)
        for name, key in (
            ("offerpage", "offer"),
            ("privacypolicypage", "privacy"),
            ("cookiepolicypage", "cookies"),
            ("shippingpage", "shipping"),
        ):
            page = LegalPage.objects.get(key=key)
            listing = reverse(f"admin:content_{name}_changelist")
            change = reverse(f"admin:content_{name}_change", args=[page.pk])
            self.assertRedirects(self.client.get(listing), change)
            form = self.client.get(change)
            self.assertEqual(form.status_code, 200)
            self.assertContains(form, "Українська")
            self.assertContains(form, "English")
            self.assertContains(form, "Français")
            self.assertContains(form, "tinymce")
            self.assertContains(form, "Якщо порожньо")

    def test_sanitize_keeps_headings(self):
        raw = sections_to_html(DOCS["cookies"]()["sections"])
        cleaned = sanitize_rich_html(raw)
        self.assertIn("<h2>", cleaned)
        self.assertIn("<p>", cleaned)
        self.assertNotIn("script", cleaned)
        self.assertEqual(cleaned, sanitize_rich_html(cleaned))
