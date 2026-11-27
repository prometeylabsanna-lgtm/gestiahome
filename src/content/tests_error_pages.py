from contextlib import nullcontext
from unittest.mock import patch

from django.db import DatabaseError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import translation


class ErrorPageTests(TestCase):
    def setUp(self):
        super().setUp()
        from django.core.cache import cache

        cache.clear()

    def tearDown(self):
        from django.core.cache import cache

        cache.clear()
        super().tearDown()

    def test_500_static_copy(self):
        from src.core.views import server_error

        resp = server_error(RequestFactory().get("/"))
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Щось пішло не так", resp.content.decode())

    def test_500_survives_db_error(self):
        from src.core.views import server_error

        with patch(
            "src.content.models.SiteSettings.load",
            side_effect=DatabaseError("x"),
        ):
            resp = server_error(RequestFactory().get("/"))
        self.assertEqual(resp.status_code, 500)
        self.assertIn("На головну · Home", resp.content.decode())

    def test_404_logo_favicon_fallback(self):
        from django.core.cache import cache

        from src.content.models import SiteSettings

        cache.clear()
        with override_settings(DEBUG=False):
            resp = self.client.get("/zzz-no-such-page/")
        self.assertEqual(resp.status_code, 404)
        html = resp.content.decode()
        self.assertIn("images/favicon.ico", html)
        self.assertIn("util-page__logo", html)
        self.assertIn("5493c.png", html)
        # The header may still use SiteSettings.logo; the 404 mark must stay 5493c.
        util = html.split("util-page__logo", 1)[1].split("</a>", 1)[0]
        self.assertIn("5493c.png", util)
        self.assertNotIn("gestia-logo-nd.png", util)

    def test_footer_nav_all_from_settings(self):
        from django.core.cache import cache

        from src.content.footer_nav import build_footer_columns
        from src.content.models import SiteSettings

        active = (translation.get_language() or "uk").split("-")[0]
        lang = translation.override("uk") if active != "uk" else nullcontext()
        with lang:
            site = SiteSettings.load()
            site.nav_all_uk = "Весь каталог"
            site.save()
            cache.clear()
            cols = build_footer_columns()
            self.assertEqual(cols["category"][0].label, "Весь каталог")

    def test_500_shows_error_page_title(self):
        from django.core.cache import cache

        from src.content.models_errors import ErrorPage
        from src.core.views import server_error

        cache.clear()
        page = ErrorPage.load()
        page.title_uk = "Тест збою"
        page.save()
        cache.clear()
        with translation.override("uk"):
            resp = server_error(RequestFactory().get("/"))
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Тест збою", resp.content.decode())
        cache.clear()

    def test_error_page_admin_changelist(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        user = get_user_model().objects.create_superuser(
            "errpage",
            "err@example.com",
            "pass-word-9",
        )
        self.client.force_login(user)
        resp = self.client.get(reverse("admin:content_errorpage_changelist"), follow=True)
        self.assertEqual(resp.status_code, 200)

    def test_footer_contacts_label_from_nav_contacts(self):
        from django.core.cache import cache

        from src.content.footer_nav import build_footer_columns
        from src.content.models import FooterLink, SiteSettings

        FooterLink.objects.filter(column="info").delete()
        site = SiteSettings.load()
        site.nav_contacts_uk = "Звʼязок"
        site.save()
        cache.clear()
        with translation.override("uk"):
            columns = build_footer_columns()
        self.assertEqual(columns["info"][-1].label, "Звʼязок")
