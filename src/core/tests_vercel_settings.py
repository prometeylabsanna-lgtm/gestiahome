"""Contract + isolated smoke tests for config.settings.vercel (zero-env demo)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

ROOT = Path(settings.BASE_DIR)
VERCEL_SETTINGS = ROOT / "config" / "settings" / "vercel.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable


def _isolated_env(**extra: str) -> dict[str, str]:
    """Minimal env; empty SECRET_KEY overrides a local .env so demo key is used."""
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "DJANGO_SETTINGS_MODULE": "config.settings.vercel",
        "VERCEL": "1",
        "SECRET_KEY": "",
        "ALLOWED_HOSTS": "",
        "CSRF_TRUSTED_ORIGINS": "",
        "SITE_URL": "",
        "DATABASE_URL": "",
        "ADMIN_URL": "",
        "SECURE_SSL_REDIRECT": "False",
    }
    env.update(extra)
    return env


class VercelSettingsSourceTests(SimpleTestCase):
    def test_demo_secret_key_contract(self):
        text = VERCEL_SETTINGS.read_text(encoding="utf-8")
        self.assertIn("DEMO_SECRET_KEY", text)
        self.assertIn("demo only, Vercel test project", text)
        self.assertIn('SECRET_KEY = _secret or DEMO_SECRET_KEY', text)
        self.assertNotIn("_BUILD_DUMMY_SECRET", text)
        self.assertNotIn("_is_build_phase", text)
        self.assertNotIn(
            "SECRET_KEY must be set in the Vercel Environment Variables UI",
            text,
        )
        self.assertIn("ENSURE_DEMO_SUPERUSER_ON_START = False", text)
        self.assertIn(
            'SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"',
            text,
        )
        self.assertIn('".vercel.app"', text)
        self.assertIn('"localhost"', text)
        self.assertIn('"127.0.0.1"', text)
        self.assertIn('"https://*.vercel.app"', text)

    def test_wsgi_does_not_auto_ensure_superuser(self):
        wsgi = (ROOT / "config" / "wsgi.py").read_text(encoding="utf-8")
        self.assertNotIn("ensure_demo_superuser", wsgi)


class VercelSettingsIsolatedTests(SimpleTestCase):
    def test_zero_secret_uses_demo_key_and_hosts(self):
        script = (
            "import os, django\n"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "from config.settings.vercel import DEMO_SECRET_KEY\n"
            "assert settings.SECRET_KEY == DEMO_SECRET_KEY\n"
            "assert settings.DEBUG is False\n"
            "assert '.vercel.app' in settings.ALLOWED_HOSTS\n"
            "assert 'localhost' in settings.ALLOWED_HOSTS\n"
            "assert '127.0.0.1' in settings.ALLOWED_HOSTS\n"
            "assert 'https://*.vercel.app' in settings.CSRF_TRUSTED_ORIGINS\n"
            "assert settings.ENSURE_DEMO_SUPERUSER_ON_START is False\n"
            "assert settings.ADMIN_URL == 'admin/'\n"
            "print(bool(settings.SECRET_KEY), settings.DEBUG, settings.ALLOWED_HOSTS[:3])\n"
        )
        proc = subprocess.run(
            [PYTHON, "-c", script],
            cwd=str(ROOT),
            env=_isolated_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("True False", proc.stdout)

    def test_vercel_url_hosts_and_site_url(self):
        script = (
            "import django\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "assert 'demo.vercel.app' in settings.ALLOWED_HOSTS\n"
            "assert 'https://demo.vercel.app' in settings.CSRF_TRUSTED_ORIGINS\n"
            "assert settings.SITE_URL == 'https://demo.vercel.app'\n"
            "print('ok')\n"
        )
        proc = subprocess.run(
            [PYTHON, "-c", script],
            cwd=str(ROOT),
            env=_isolated_env(
                VERCEL_URL="demo.vercel.app",
                VERCEL_PROJECT_PRODUCTION_URL="demo.vercel.app",
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ok", proc.stdout)

    def test_manage_check_and_pages_under_vercel_host(self):
        check = subprocess.run(
            [PYTHON, "manage.py", "check"],
            cwd=str(ROOT),
            env=_isolated_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr + check.stdout)

        script = (
            "import django\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "from django.test import Client, override_settings\n"
            "# Local smoke without collectstatic; Vercel build has a manifest.\n"
            "storage = {\n"
            "    'default': settings.STORAGES['default'],\n"
            "    'staticfiles': {\n"
            "        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',\n"
            "    },\n"
            "}\n"
            "host = 'gestiahome-pro-m.vercel.app'\n"
            "with override_settings(STORAGES=storage, STATICFILES_STORAGE="
            "'django.contrib.staticfiles.storage.StaticFilesStorage'):\n"
            "    c = Client()\n"
            "    for path in ('/', '/katalog/'):\n"
            "        r = c.get(path, HTTP_HOST=host, secure=True)\n"
            "        assert r.status_code == 200, (path, r.status_code)\n"
            "print('pages-ok')\n"
        )
        pages = subprocess.run(
            [PYTHON, "-c", script],
            cwd=str(ROOT),
            env=_isolated_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(pages.returncode, 0, pages.stderr)
        self.assertIn("pages-ok", pages.stdout)
