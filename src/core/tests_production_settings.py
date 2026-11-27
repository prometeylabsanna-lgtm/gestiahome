"""Isolated smoke tests for config.settings.production (Droplet)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

ROOT = Path(settings.BASE_DIR)
PRODUCTION_SETTINGS = ROOT / "config" / "settings" / "production.py"
WSGI = ROOT / "config" / "wsgi.py"
PYTHON = (
    str(ROOT / ".venv" / "bin" / "python")
    if (ROOT / ".venv" / "bin" / "python").is_file()
    else sys.executable
)


def _isolated_env(**extra: str) -> dict[str, str]:
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "DJANGO_SETTINGS_MODULE": "config.settings.production",
        "SECRET_KEY": "dummy-production-secret-key-for-test",
        "DATABASE_URL": "postgres://u:p@localhost:5432/db",
        "ALLOWED_HOSTS": "example.com,127.0.0.1,localhost,backend",
        "LIQPAY_SANDBOX": "0",
        "LIQPAY_PUBLIC_KEY": "",
        "LIQPAY_PRIVATE_KEY": "",
        "SECURE_SSL_REDIRECT": "0",
        "SECURE_HSTS_SECONDS": "0",
        "SECURE_HSTS_INCLUDE_SUBDOMAINS": "0",
        "CSRF_TRUSTED_ORIGINS": "",
        "CSP_REPORT_ONLY": "1",
        "TRUST_X_FORWARDED_FOR": "1",
        "SITE_URL": "https://example.com",
        "ADMIN_URL": "gestia-staff/",
        "USE_HTTPS": "0",
        "SESSION_COOKIE_SECURE": "0",
        "CSRF_COOKIE_SECURE": "0",
        "EMAIL_HOST": "",
        "DEFAULT_FROM_EMAIL": "shop@example.com",
        "ORDER_NOTIFY_EMAIL": "",
        "TELEGRAM_BOT_TOKEN": "",
        "TELEGRAM_CHAT_ID": "",
        "NOVA_POSHTA_API_KEY": "",
    }
    env.update(extra)
    return env


def _run(code: str, **extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, "-c", code],
        cwd=str(ROOT),
        env=_isolated_env(**extra),
        capture_output=True,
        text=True,
        check=False,
    )


_PRINT_FLAGS = (
    "import config.settings.production as s\n"
    "print('USE_HTTPS', s.USE_HTTPS)\n"
    "print('SESSION', s.SESSION_COOKIE_SECURE)\n"
    "print('CSRF', s.CSRF_COOKIE_SECURE)\n"
    "print('REDIRECT', s.SECURE_SSL_REDIRECT)\n"
    "print('ADMIN', s.ADMIN_URL)\n"
    "print('EMAIL', s.EMAIL_BACKEND)\n"
    "print('TRUST', s.TRUST_X_FORWARDED_FOR)\n"
)


class ProductionSettingsSourceTests(SimpleTestCase):
    def test_cookies_default_to_use_https(self):
        text = PRODUCTION_SETTINGS.read_text(encoding="utf-8")
        self.assertIn('config("USE_HTTPS", default=True, cast=bool)', text)
        self.assertIn("default=USE_HTTPS", text)
        self.assertIn("SECURE_SSL_REDIRECT = False", text)
        self.assertIn("CSP_REPORT_ONLY = False", text)
        self.assertNotIn(
            "SECURE_SSL_REDIRECT = config(",
            text,
        )

    def test_wsgi_has_no_vercel_or_whitenoise(self):
        text = WSGI.read_text(encoding="utf-8")
        self.assertNotIn("VERCEL", text)
        self.assertNotIn("WhiteNoise", text)
        self.assertNotIn("whitenoise", text)
        self.assertIn("config.settings.production", text)


class ProductionSettingsImportTests(SimpleTestCase):
    def test_https_cookies_are_the_default(self):
        env = _isolated_env()
        for key in ("USE_HTTPS", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE"):
            env.pop(key, None)
        result = subprocess.run(
            [PYTHON, "-c", _PRINT_FLAGS],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("USE_HTTPS True", result.stdout)
        self.assertIn("SESSION True", result.stdout)
        self.assertIn("CSRF True", result.stdout)
        self.assertIn("REDIRECT False", result.stdout)

    def test_http_cookies_and_no_gunicorn_redirect(self):
        result = _run(_PRINT_FLAGS, USE_HTTPS="0")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("USE_HTTPS False", result.stdout)
        self.assertIn("SESSION False", result.stdout)
        self.assertIn("CSRF False", result.stdout)
        self.assertIn("REDIRECT False", result.stdout)
        self.assertIn("ADMIN gestia-staff/", result.stdout)
        self.assertIn("TRUST True", result.stdout)

    def test_https_cookies_keep_redirect_off(self):
        result = _run(
            _PRINT_FLAGS,
            USE_HTTPS="1",
            SESSION_COOKIE_SECURE="1",
            CSRF_COOKIE_SECURE="1",
            SECURE_SSL_REDIRECT="1",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("USE_HTTPS True", result.stdout)
        self.assertIn("SESSION True", result.stdout)
        self.assertIn("CSRF True", result.stdout)
        self.assertIn("REDIRECT False", result.stdout)

    def test_default_admin_url_rejected(self):
        result = _run("import config.settings.production\n", ADMIN_URL="admin/")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ADMIN_URL", result.stderr)

    def test_smtp_when_email_host_set(self):
        result = _run(_PRINT_FLAGS, EMAIL_HOST="smtp.example.com")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("EMAIL django.core.mail.backends.smtp.EmailBackend", result.stdout)

    def test_wsgi_ignores_vercel_env(self):
        env = _isolated_env()
        env.pop("DJANGO_SETTINGS_MODULE", None)
        env["VERCEL"] = "1"
        code = (
            "import config.wsgi as w\n"
            "from django.conf import settings\n"
            "from django.core.handlers.wsgi import WSGIHandler\n"
            "print(isinstance(w.application, WSGIHandler))\n"
            "print(settings.SETTINGS_MODULE)\n"
        )
        result = subprocess.run(
            [PYTHON, "-c", code],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("True", result.stdout)
        self.assertIn("config.settings.production", result.stdout)
