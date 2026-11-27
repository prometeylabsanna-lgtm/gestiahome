import os

from django.core.wsgi import get_wsgi_application


def _default_settings_module() -> str:
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    return "config.settings.production"


os.environ.setdefault("DJANGO_SETTINGS_MODULE", _default_settings_module())

application = get_wsgi_application()
