from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Підкласи (develop / production) задають або перевіряють ключ.
# Порожній default — імпорт base не вимагає .env, доки модуль середовища не перевірить ключ.
SECRET_KEY = config("SECRET_KEY", default="")

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.forms",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "src.core.axes_config.AxesUkConfig",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "tinymce",
    "src.core",
    "src.content",
    "src.catalog",
    "src.commerce",
]

MIDDLEWARE = [
    "src.core.middleware.AdminRobotsTagMiddleware",
    "src.core.middleware.ContentSecurityPolicyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "src.core.middleware.AdminUkrainianMiddleware",
    "src.core.middleware.LanguagePrefixMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "src.core.context_processors.shop",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "transaction_mode": "IMMEDIATE",
            "timeout": 20,
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Django 5.2: PBKDF2PasswordHasher робить 1_000_000 ітерацій. Перший хешер — для нових паролів.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

LANGUAGE_CODE = "uk"
LANGUAGES = [
    ("uk", "Українська"),
    ("en", "English"),
    ("fr", "Français"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="shop@example.com")
ORDER_NOTIFY_EMAIL = config("ORDER_NOTIFY_EMAIL", default="")
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID", default="")
NOVA_POSHTA_API_KEY = config("NOVA_POSHTA_API_KEY", default="")
LIQPAY_PUBLIC_KEY = str(config("LIQPAY_PUBLIC_KEY", default="") or "").strip()
LIQPAY_PRIVATE_KEY = str(config("LIQPAY_PRIVATE_KEY", default="") or "").strip()
LIQPAY_SANDBOX = config("LIQPAY_SANDBOX", default=False, cast=bool)
LIQPAY_ALLOW_SHA1_FALLBACK = config("LIQPAY_ALLOW_SHA1_FALLBACK", default=True, cast=bool)

# Тимчасовий залишок активних товарів, доки адміністратор не виставить реальні кількості.
STOCK_PLACEHOLDER_QTY = 10
# Карткове замовлення тримає залишок, доки LiqPay не підтвердить оплату або не мине цей термін.
CARD_STOCK_HOLD_HOURS = 24

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "gestia_cache",
    }
}

# Per-form overrides use the same shape. Missing keys fall back to "default".
# Кошик і Нова пошта мають вищі стелі: 5/600 зупинило б набір міста і кількість у кошику.
RATE_LIMITS = {
    "default": {"limit": 5, "window": 600},
    "np": {"limit": 120, "window": 600},
    "cart": {"limit": 60, "window": 600},
    "wishlist": {"limit": 60, "window": 600},
}

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=60)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = [["ip_address"], ["username"]]
TRUST_X_FORWARDED_FOR = config("TRUST_X_FORWARDED_FOR", default=False, cast=bool)


def _normalize_admin_url(raw: str) -> str:
    value = str(raw or "").strip().strip("/")
    if not value:
        return "admin/"
    return f"{value}/"


ADMIN_URL = _normalize_admin_url(config("ADMIN_URL", default="admin/"))

# Порожній рядок: canonical і sitemap беруть scheme + host запиту.
SITE_URL = str(config("SITE_URL", default="") or "").strip().rstrip("/")

# Public pages load Google Fonts and have no inline scripts or map iframes.
# Develop лишає report-only. Production вимикає його для вітрини.
CSP_REPORT_ONLY = config("CSP_REPORT_ONLY", default=True, cast=bool)
CSP_POLICY = "; ".join(
    [
        "default-src 'self'",
        "base-uri 'self'",
        "form-action 'self' https://www.liqpay.ua",
        "frame-ancestors 'none'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com",
    ]
)
# Unfold і TinyMCE потребують інлайн-скриптів. Політика завжди enforcing, окремо від вітрини.
CSP_POLICY_ADMIN = "; ".join(
    [
        "default-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: blob: https:",
        "connect-src 'self'",
    ]
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "src": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

def _admin_asset(path):
    def href(request):
        from django.templatetags.static import static

        return static(path)

    return href


TINYMCE_DEFAULT_CONFIG = {
    "height": 280,
    "width": "100%",
    "menubar": False,
    "branding": False,
    "promotion": False,
    "statusbar": False,
    "plugins": "link lists",
    "toolbar": (
        "undo redo | bold italic underline | bullist numlist | link | "
        "blocks | blockquote | removeformat"
    ),
    "block_formats": "Абзац=p; Заголовок 2=h2; Заголовок 3=h3; Заголовок 4=h4",
    "language": "uk",
    "forced_root_block": "p",
    "newline_behavior": "block",
    "valid_elements": (
        "p,br,strong/b,em/i,u,a[href|target|rel],ul,ol,li,h2,h3,h4,blockquote,span"
    ),
    "link_default_target": "_blank",
    "link_default_rel": "noopener noreferrer",
    "content_style": (
        "body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; "
        "font-size: 16px; line-height: 1.5; margin: 8px; }"
        "p { margin: 0 0 0.75em; }"
    ),
}

TINYMCE_SHORT_CONFIG = {
    **TINYMCE_DEFAULT_CONFIG,
    "height": 160,
    "toolbar": "undo redo | bold italic underline | bullist | link | removeformat",
    "valid_elements": "p,br,strong/b,em/i,u,a[href|target|rel],ul,li",
}

UNFOLD = {
    "SITE_TITLE": "Адміністрування сайту",
    "SITE_HEADER": "Адміністрування сайту",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": _admin_asset("images/favicon.png"),
        "dark": _admin_asset("images/favicon.png"),
    },
    "SITE_FAVICONS": [
        {
            "href": _admin_asset("images/favicon.ico"),
            "rel": "icon",
            "sizes": "any",
        },
        {
            "href": _admin_asset("images/favicon.png"),
            "rel": "icon",
            "type": "image/png",
        },
        {
            "href": _admin_asset("images/apple-touch-icon.png"),
            "rel": "apple-touch-icon",
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_LANGUAGES": False,
    "STYLES": [
        _admin_asset("css/admin/char_counter.css"),
        _admin_asset("css/admin/image_preview.css"),
        _admin_asset("css/admin/color_picker.css"),
        _admin_asset("css/admin/brand.css"),
        _admin_asset("css/admin/forms.css"),
    ],
    "SCRIPTS": [
        _admin_asset("js/admin/char_counter.js"),
        _admin_asset("js/admin/color_picker.js"),
    ],
    "COLORS": {
        "base": {
            "50": "#ffffff",
            "100": "#f5f5f5",
            "200": "#e5e5e5",
            "300": "#d4d4d4",
            "400": "#a3a3a3",
            "500": "#737373",
            "600": "#525252",
            "700": "#404040",
            "800": "#262626",
            "900": "#171717",
            "950": "#000000",
        },
        "primary": {
            "50": "#fff5f5",
            "100": "#ffe3e3",
            "200": "#ffc9c9",
            "300": "#ffa2a2",
            "400": "#f87171",
            "500": "#ef4444",
            "600": "#dc2626",
            "700": "#b91c1c",
            "800": "#991b1b",
            "900": "#7f1d1d",
            "950": "#450a0a",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-900)",
            "default-dark": "var(--color-base-100)",
            "important-light": "var(--color-base-950)",
            "important-dark": "var(--color-base-50)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": "src.core.admin_nav.build_navigation",
    },
}
