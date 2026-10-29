"""Vercel demo/production settings. No Postgres required for free demo."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import BASE_DIR, MIDDLEWARE

logger = logging.getLogger(__name__)

DEBUG = False

DEMO_DB_SOURCE = BASE_DIR / "demo" / "gestia_demo.sqlite3"
DEMO_DB_RUNTIME = Path("/tmp/gestia_demo.sqlite3")
_BUILD_DUMMY_SECRET = "vercel-build-only-not-for-runtime-use"


def _is_build_phase() -> bool:
    if os.environ.get("DJANGO_BUILD_PHASE") == "1":
        return True
    argv = [str(item).lower() for item in sys.argv]
    if any(item == "collectstatic" or item.endswith("collectstatic") for item in argv):
        return True
    # Vercel: CI=1 лише на build; VERCEL=1 і на runtime.
    if os.environ.get("VERCEL") == "1" and os.environ.get("CI") == "1":
        return True
    return False


def _strip_host(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if "://" not in value:
        return value.split("/")[0].strip()
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return (parsed.hostname or "").strip()


def _https_origin(host: str) -> str:
    host = _strip_host(host)
    return f"https://{host}" if host else ""


_secret = (config("SECRET_KEY", default="") or "").strip()
if _secret:
    SECRET_KEY = _secret
elif _is_build_phase():
    SECRET_KEY = _BUILD_DUMMY_SECRET
else:
    raise ImproperlyConfigured(
        "SECRET_KEY must be set in the Vercel Environment Variables UI "
        "(Project → Settings → Environment Variables)."
    )

_hosts: list[str] = [
    item.strip()
    for item in config("ALLOWED_HOSTS", default="", cast=Csv())
    if item and item.strip()
]
_hosts.append(".vercel.app")
for _var in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL", "VERCEL_BRANCH_URL"):
    _host = _strip_host(os.environ.get(_var, ""))
    if _host:
        _hosts.append(_host)
ALLOWED_HOSTS = list(dict.fromkeys(_hosts))

_csrf: list[str] = [
    item.strip().rstrip("/")
    for item in config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
    if item and item.strip()
]
for _host in ALLOWED_HOSTS:
    if _host.startswith("."):
        continue
    _origin = _https_origin(_host)
    if _origin:
        _csrf.append(_origin)
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(_csrf))

_site = (config("SITE_URL", default="") or "").strip().rstrip("/")
if not _site:
    _runtime_host = _strip_host(
        os.environ.get("VERCEL_PROJECT_PRODUCTION_URL")
        or os.environ.get("VERCEL_URL")
        or ""
    )
    if _runtime_host:
        _site = _https_origin(_runtime_host)
SITE_URL = _site

ADMIN_URL = _normalize_admin_url(config("ADMIN_URL", default="admin/"))  # noqa: F405

_database_url = (config("DATABASE_URL", default="") or "").strip()
if _database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    if not DEMO_DB_SOURCE.is_file():
        raise ImproperlyConfigured(
            f"Demo SQLite missing at {DEMO_DB_SOURCE}. "
            "Run: python manage.py build_demo_db"
        )
    if not DEMO_DB_RUNTIME.is_file():
        shutil.copy2(DEMO_DB_SOURCE, DEMO_DB_RUNTIME)
        logger.warning(
            "Demo DB copied to %s (ephemeral — writes are lost on cold start).",
            DEMO_DB_RUNTIME,
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DEMO_DB_RUNTIME),
            "OPTIONS": {
                "transaction_mode": "IMMEDIATE",
                "timeout": 20,
            },
        }
    }

MIDDLEWARE = list(MIDDLEWARE)
_security_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(
        _security_idx + 1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

_aws_bucket = (config("AWS_STORAGE_BUCKET_NAME", default="") or "").strip()
if _aws_bucket:
    AWS_STORAGE_BUCKET_NAME = _aws_bucket
    AWS_S3_ENDPOINT_URL = (config("AWS_S3_ENDPOINT_URL", default="") or "").strip() or None
    AWS_S3_CUSTOM_DOMAIN = (config("AWS_S3_CUSTOM_DOMAIN", default="") or "").strip() or None
    AWS_S3_REGION_NAME = (config("AWS_S3_REGION_NAME", default="") or "").strip() or None
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                **(
                    {"endpoint_url": AWS_S3_ENDPOINT_URL}
                    if AWS_S3_ENDPOINT_URL
                    else {}
                ),
                **(
                    {"custom_domain": AWS_S3_CUSTOM_DOMAIN}
                    if AWS_S3_CUSTOM_DOMAIN
                    else {}
                ),
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    MEDIA_ROOT = Path("/tmp/media")
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    logger.warning(
        "MEDIA_ROOT=%s is ephemeral on Vercel; demo assets are served from "
        "public/media via CDN. Set AWS_STORAGE_BUCKET_NAME for persistent media.",
        MEDIA_ROOT,
    )
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": str(MEDIA_ROOT),
                "base_url": MEDIA_URL,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Strict"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
    cast=bool,
)
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
TRUST_X_FORWARDED_FOR = config("TRUST_X_FORWARDED_FOR", default=True, cast=bool)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "src": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Cold-start hook flag for wsgi.py (ORM needs apps ready).
ENSURE_DEMO_SUPERUSER_ON_START = not bool(_database_url)
