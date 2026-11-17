import importlib
import re
from html import escape

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.content.models import AboutPage

ABOUT_TITLE_EN = "Hi, I\u2019m Gestia"


class AboutTitleEnMigrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.migration = importlib.import_module(
            "src.content.migrations.0044_about_title_en"
        )
        self.page = AboutPage.load()
        self.page.title_uk = ABOUT_TITLE_EN
        self.page.intro_text_en = "<p>Keep intro EN</p>"
        self.page.save()

    def test_forward_updates_about_and_padded_about(self):
        for raw in ("About", " About "):
            self.page.title_en = raw
            self.page.save(update_fields=["title_en"])
            self.migration.forward(apps, None)
            self.page.refresh_from_db()
            self.assertEqual(self.page.title_en, ABOUT_TITLE_EN)

    def test_forward_skips_other_and_empty_values(self):
        self.page.title_en = "Custom title"
        self.page.save(update_fields=["title_en"])
        self.migration.forward(apps, None)
        self.page.refresh_from_db()
        self.assertEqual(self.page.title_en, "Custom title")

        self.page.title_en = ""
        self.page.save(update_fields=["title_en"])
        self.migration.forward(apps, None)
        self.page.refresh_from_db()
        self.assertEqual(self.page.title_en, "")

    def test_forward_does_not_change_other_fields(self):
        self.page.title_uk = "UK title keep"
        self.page.title_en = "About"
        self.page.intro_text_en = "<p>Intro keep</p>"
        self.page.save(update_fields=["title_uk", "title_en", "intro_text_en"])
        self.migration.forward(apps, None)
        self.page.refresh_from_db()
        self.assertEqual(self.page.title_en, ABOUT_TITLE_EN)
        self.assertEqual(self.page.title_uk, "UK title keep")
        self.assertEqual(self.page.intro_text_en, "<p>Intro keep</p>")

    def test_en_about_renders_h1_with_title_en(self):
        self.page.title_en = ABOUT_TITLE_EN
        self.page.save(update_fields=["title_en"])
        cache.clear()
        response = self.client.get("/en/pro-nas/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        title_variants = {ABOUT_TITLE_EN, escape(ABOUT_TITLE_EN)}
        self.assertTrue(
            any(v in body for v in title_variants),
            "h1 title text missing (raw or escaped)",
        )
        pattern = (
            r'<h1[^>]*id="about-title"[^>]*>\s*(?:'
            + "|".join(re.escape(v) for v in title_variants)
            + r")\s*</h1>"
        )
        self.assertRegex(body, pattern)


class AboutNdRenderTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("uk")
        self.page = AboutPage.load()
        self.page.title_uk = "Hi, I’m Gestia"
        self.page.intro_text_uk = "<p>Текст інтро з <em>акцентом</em>.</p>"
        self.page.gestia_quote_uk = "ЦИТАТА ГЕСТІЇ"
        self.page.approach_text_uk = "Текст підходу"
        self.page.together_text_uk = "<p>Текст разом</p>"
        self.page.closing_text_uk = "<p>Фінальний абзац</p>"
        self.page.cta_uk = "Перейти до каталогу"
        self.page.seo_title_uk = "SEO About"
        self.page.seo_description_uk = "SEO desc about"
        self.page.save()

    def test_about_renders_cms_fields(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hi, I’m Gestia")
        self.assertContains(response, "Текст інтро з")
        self.assertContains(response, "акцентом")
        self.assertContains(response, "ЦИТАТА ГЕСТІЇ")
        self.assertContains(response, "Текст підходу")
        self.assertContains(response, "Текст разом")
        self.assertContains(response, "Фінальний абзац")
        self.assertContains(response, "Перейти до каталогу")
        self.assertContains(response, 'href="' + reverse("catalog") + '"')
        self.assertContains(response, "css/nd/about.css")
        self.assertNotContains(response, "css/pages/about.css")
        self.assertNotContains(response, "Популярні товари")
        self.assertNotContains(response, 'class="about-reviews"')

    def test_about_field_change_updates_render(self):
        self.page.title_uk = "Новий заголовок"
        self.page.cta_uk = "Каталог уже"
        self.page.save()
        cache.clear()
        response = self.client.get(reverse("about"))
        self.assertContains(response, "Новий заголовок")
        self.assertContains(response, "Каталог уже")
        self.assertNotContains(response, "Hi, I’m Gestia")

    def test_about_english_falls_back_to_uk_when_en_empty(self):
        self.page.title_en = ""
        self.page.intro_text_en = ""
        self.page.save()
        cache.clear()
        response = self.client.get("/en/pro-nas/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hi, I’m Gestia")
        self.assertContains(response, "Текст інтро з")

    def test_about_english_uses_en_fields(self):
        self.page.title_en = "Hello Gestia"
        self.page.intro_text_en = "<p>English intro</p>"
        self.page.cta_en = "Go to catalogue"
        self.page.save()
        cache.clear()
        response = self.client.get("/en/pro-nas/")
        self.assertContains(response, "Hello Gestia")
        self.assertContains(response, "English intro")
        self.assertContains(response, "Go to catalogue")
        self.assertNotContains(response, "Hi, I’m Gestia")


class AboutNdAdminTests(TestCase):
    def setUp(self):
        cache.clear()
        user_model = get_user_model()
        self.user = user_model.objects.create_superuser(
            username="about-admin",
            email="about-admin@example.com",
            password="pass",
        )
        self.client.force_login(self.user)
        AboutPage.load()

    def test_about_admin_blocks_open(self):
        urls = [
            "admin:content_aboutintro_changelist",
            "admin:content_aboutgestia_changelist",
            "admin:content_aboutapproach_changelist",
            "admin:content_abouttogether_changelist",
            "admin:content_aboutclosing_changelist",
        ]
        for name in urls:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            follow = self.client.get(reverse(name), follow=True)
            self.assertEqual(follow.status_code, 200, name)
