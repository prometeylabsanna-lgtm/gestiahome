import os

from django.core.wsgi import get_wsgi_application


def _default_settings_module() -> str:
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    if os.environ.get("VERCEL"):
        return "config.settings.vercel"
    return "config.settings.production"


os.environ.setdefault("DJANGO_SETTINGS_MODULE", _default_settings_module())

application = get_wsgi_application()
# Vercel Python / деякі runtime очікують імʼя `app`.
app = application

from django.conf import settings  # noqa: E402

if getattr(settings, "ENSURE_DEMO_SUPERUSER_ON_START", False):
    from src.core.demo_runtime import ensure_demo_superuser

    ensure_demo_superuser()
