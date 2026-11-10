"""Contract + isolated smoke tests for config.settings.vercel (SECRET_KEY from env)."""

from __future__ import annotations

import os
import secrets
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
    """Minimal env with a random per-test SECRET_KEY (overrides a local .env)."""
    env = {
        "HOME": os.environ.get("HOME", ""),
        "PATH": os.environ.get("PATH", ""),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "DJANGO_SETTINGS_MODULE": "config.settings.vercel",
        "VERCEL": "1",
        "SECRET_KEY": "test-" + secrets.token_urlsafe(32),
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
    def test_no_hardcoded_secret_key_contract(self):
        text = VERCEL_SETTINGS.read_text(encoding="utf-8")
        self.assertNotIn("DEMO_SECRET_KEY", text)
        self.assertIn("SECRET_KEY must be set in the Vercel Environment Variables", text)
        self.assertIn('os.environ.get("DJANGO_BUILD_PHASE") == "1"', text)
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
    def test_missing_secret_fails_at_runtime(self):
        proc = subprocess.run(
            [PYTHON, "-c", "import django; django.setup()"],
            cwd=str(ROOT),
            env=_isolated_env(SECRET_KEY=""),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("SECRET_KEY must be set", proc.stderr)

    def test_missing_secret_ok_in_build_phase(self):
        script = (
            "import django\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "assert settings.SECRET_KEY.startswith('build-only-')\n"
            "print('build-ok')\n"
        )
        proc = subprocess.run(
            [PYTHON, "-c", script],
            cwd=str(ROOT),
            env=_isolated_env(SECRET_KEY="", DJANGO_BUILD_PHASE="1"),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("build-ok", proc.stdout)

    def test_env_secret_used_and_hosts(self):
        script = (
            "import os, django\n"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')\n"
            "django.setup()\n"
            "from django.conf import settings\n"
            "assert settings.SECRET_KEY == os.environ['SECRET_KEY']\n"
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
