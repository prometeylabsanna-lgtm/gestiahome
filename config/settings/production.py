from urllib.parse import unquote, urlparse

from decouple import config
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import ADMIN_URL as _ADMIN_URL
from .base import LIQPAY_SANDBOX as _LIQPAY_SANDBOX
from .base import SECRET_KEY as _BASE_SECRET_KEY

DEBUG = False

if not (_BASE_SECRET_KEY or "").strip():
    raise ImproperlyConfigured("SECRET_KEY is required for production settings.")

if _LIQPAY_SANDBOX:
    raise ImproperlyConfigured("LIQPAY_SANDBOX must be off in production")

if str(_ADMIN_URL or "").strip().strip("/") == "admin":
    raise ImproperlyConfigured(
        "ADMIN_URL must not stay at the default admin/ in production."
    )

_db_url = (config("DATABASE_URL", default="") or "").strip()
if not _db_url:
    raise ImproperlyConfigured("DATABASE_URL is required for production settings.")
_db = urlparse(_db_url)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db.path.lstrip("/"),
        "USER": unquote(_db.username or ""),
        "PASSWORD": unquote(_db.password or ""),
        "HOST": _db.hostname,
        "PORT": _db.port or 5432,
        "CONN_MAX_AGE": 60,
    }
}

USE_HTTPS = config("USE_HTTPS", default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
# TLS terminates in nginx. Gunicorn stays on HTTP so /healthz/ is not 301.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = config(
    "SESSION_COOKIE_SECURE", default=USE_HTTPS, cast=bool
)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=USE_HTTPS, cast=bool)
# Lax keeps the cart session on the first top-level visit from Instagram,
# Telegram, or Google. Strict dropped the cookie on that cross-site GET.
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
# HTMX copies the token from <meta name="csrf-token">, not from the CSRF cookie.
CSRF_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)
# nginx sets X-Forwarded-For to $remote_addr; trust that hop in production.
TRUST_X_FORWARDED_FOR = config("TRUST_X_FORWARDED_FOR", default=True, cast=bool)
AXES_CLIENT_IP_CALLABLE = "src.core.ratelimit.client_ip"
# Вітрина завжди enforcing. Адмінка має окрему політику в middleware.
CSP_REPORT_ONLY = False

_email_host = (config("EMAIL_HOST", default="") or "").strip()
if _email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _email_host
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
