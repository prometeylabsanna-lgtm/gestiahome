from importlib import reload

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import clear_url_caches, set_urlconf

from config.settings.base import _normalize_admin_url
from src.core.ratelimit import client_ip, honeypot_filled, is_rate_limited


def _restore_urls():
    import config.urls as root_urls

    reload(root_urls)
    clear_url_caches()
    set_urlconf(None)


class RateLimitHelperTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_blocks_after_quota_per_form(self):
        request = RequestFactory().post("/")
        limits = {"default": {"limit": 2, "window": 600}}
        with override_settings(RATE_LIMITS=limits):
            self.assertFalse(is_rate_limited(request, "callback"))
            self.assertFalse(is_rate_limited(request, "callback"))
            self.assertTrue(is_rate_limited(request, "callback"))
            self.assertFalse(is_rate_limited(request, "home"))

    def test_remote_addr_when_forwarded_header_is_untrusted(self):
        request = RequestFactory().post(
            "/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="203.0.113.8, 10.0.0.1",
        )
        with override_settings(TRUST_X_FORWARDED_FOR=False):
            self.assertEqual(client_ip(request), "192.0.2.10")

    def test_first_forwarded_hop_when_trusted(self):
        request = RequestFactory().post(
            "/",
            REMOTE_ADDR="192.0.2.10",
            HTTP_X_FORWARDED_FOR="203.0.113.8, 10.0.0.1",
        )
        with override_settings(TRUST_X_FORWARDED_FOR=True):
            self.assertEqual(client_ip(request), "203.0.113.8")

    def test_untrusted_forwarded_for_shares_one_bucket(self):
        factory = RequestFactory()
        first = factory.post("/", REMOTE_ADDR="192.0.2.4", HTTP_X_FORWARDED_FOR="203.0.113.1")
        second = factory.post("/", REMOTE_ADDR="192.0.2.4", HTTP_X_FORWARDED_FOR="203.0.113.2")
        limits = {"default": {"limit": 1, "window": 600}}
        with override_settings(TRUST_X_FORWARDED_FOR=False, RATE_LIMITS=limits):
            self.assertFalse(is_rate_limited(first, "contact"))
            self.assertTrue(is_rate_limited(second, "contact"))

    def test_trusted_forwarded_for_splits_buckets(self):
        factory = RequestFactory()
        first = factory.post("/", REMOTE_ADDR="127.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.1")
        other = factory.post("/", REMOTE_ADDR="127.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.2")
        same = factory.post("/", REMOTE_ADDR="127.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.1, 10.1.1.1")
        limits = {"default": {"limit": 1, "window": 600}}
        with override_settings(TRUST_X_FORWARDED_FOR=True, RATE_LIMITS=limits):
            self.assertFalse(is_rate_limited(first, "callback"))
            self.assertFalse(is_rate_limited(other, "callback"))
            self.assertTrue(is_rate_limited(same, "callback"))

    def test_honeypot_ignores_blank(self):
        factory = RequestFactory()
        self.assertFalse(honeypot_filled(factory.post("/", {})))
        self.assertFalse(honeypot_filled(factory.post("/", {"gestia_hp": "   "})))
        self.assertFalse(honeypot_filled(factory.post("/", {"website": "   "})))
        self.assertTrue(honeypot_filled(factory.post("/", {"gestia_hp": "https://spam.example"})))
        self.assertTrue(honeypot_filled(factory.post("/", {"website": "https://spam.example"})))


class CspHeaderTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_report_only_header_on_public_page(self):
        response = self.client.get("/")
        header = "Content-Security-Policy-Report-Only"
        self.assertIn(header, response)
        policy = response[header]
        self.assertIn("default-src 'self'", policy)
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertIn("form-action 'self'", policy)
        self.assertIn("script-src 'self'", policy)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", policy)
        self.assertNotIn("Content-Security-Policy", response)

    @override_settings(CSP_REPORT_ONLY=False)
    def test_enforced_header_when_report_only_disabled(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response["Content-Security-Policy"].split(";")[0], "default-src 'self'")
        self.assertNotIn("Content-Security-Policy-Report-Only", response)


class AdminUrlTests(TestCase):
    def setUp(self):
        cache.clear()

    def tearDown(self):
        _restore_urls()

    def test_normalizer_adds_a_single_trailing_slash(self):
        self.assertEqual(_normalize_admin_url("staff"), "staff/")
        self.assertEqual(_normalize_admin_url("staff/"), "staff/")
        self.assertEqual(_normalize_admin_url("/staff"), "staff/")
        self.assertEqual(_normalize_admin_url(""), "admin/")

    def test_setting_is_a_slash_terminated_route(self):
        from django.conf import settings

        self.assertTrue(settings.ADMIN_URL.endswith("/"))
        self.assertFalse(settings.ADMIN_URL.startswith("/"))

    def test_root_urlconf_uses_admin_setting(self):
        from django.conf import settings

        from config.urls import urlpatterns

        matched = False
        for entry in urlpatterns:
            route = getattr(getattr(entry, "pattern", None), "_route", None)
            if route == settings.ADMIN_URL:
                matched = True
                break
        self.assertTrue(matched)

    def test_admin_path_follows_setting(self):
        sentinel = "gestia-secure-entry/"
        try:
            with override_settings(ADMIN_URL=sentinel):
                _restore_urls()
                response = self.client.get("/" + sentinel)
                self.assertLess(response.status_code, 400)
                self.assertNotEqual(response.status_code, 404)
                missing = self.client.get("/not-the-configured-admin/")
                self.assertEqual(missing.status_code, 404)
        finally:
            _restore_urls()
