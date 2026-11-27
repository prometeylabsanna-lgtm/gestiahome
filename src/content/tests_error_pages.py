from contextlib import nullcontext
from unittest.mock import patch

from django.db import DatabaseError
from django.test import RequestFactory, TestCase, override_settings
from django.utils import translation


class ErrorPageTests(TestCase):
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
        alt = (getattr(SiteSettings.load(), "logo_alt", "") or "").strip()
        if alt:
            self.assertIn("util-page__logo", html)
            return
        self.assertIn("5493c.png", html)
        self.assertIn('aria-label="Gestia', html)

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
