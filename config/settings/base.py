from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Підкласи (develop / production / vercel) задають або перевіряють ключ.
# Порожній default — щоб імпорт base не падав на Vercel build без .env.
SECRET_KEY = config("SECRET_KEY", default="")

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.forms",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
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

LANGUAGE_CODE = "uk"
LANGUAGES = [
    ("uk", "Українська"),
    ("en", "English"),
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

# Тимчасовий залишок активних товарів, доки адміністратор не виставить реальні кількості.
STOCK_PLACEHOLDER_QTY = 10

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gestia",
    }
}

# Per-form overrides use the same shape. Missing keys fall back to "default".
RATE_LIMITS = {
    "default": {"limit": 5, "window": 600},
}
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
CSP_REPORT_ONLY = config("CSP_REPORT_ONLY", default=True, cast=bool)
CSP_POLICY = "; ".join(
    [
        "default-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com",
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
    "SITE_TITLE": "Gestia Home",
    "SITE_HEADER": "Gestia Home",
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
