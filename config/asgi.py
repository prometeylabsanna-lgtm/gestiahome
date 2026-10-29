import os

from django.core.asgi import get_asgi_application


def _default_settings_module() -> str:
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    if os.environ.get("VERCEL"):
        return "config.settings.vercel"
    return "config.settings.production"


os.environ.setdefault("DJANGO_SETTINGS_MODULE", _default_settings_module())

application = get_asgi_application()
app = application
