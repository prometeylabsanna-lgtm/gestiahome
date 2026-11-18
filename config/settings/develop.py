from decouple import config

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = config("SECRET_KEY", default="dev-only-insecure-key-do-not-use-in-prod")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gestia",
    }
}
