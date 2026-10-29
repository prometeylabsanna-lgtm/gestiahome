import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application


def _default_settings_module() -> str:
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        return os.environ["DJANGO_SETTINGS_MODULE"]
    if os.environ.get("VERCEL"):
        return "config.settings.vercel"
    return "config.settings.production"


os.environ.setdefault("DJANGO_SETTINGS_MODULE", _default_settings_module())

application = get_wsgi_application()

from django.conf import settings  # noqa: E402

# Demo media: WhiteNoise віддає committed demo/media на /media/…
# (CDN public/ — додатково на build; uploads у /tmp/media не покриває).
_demo_media = Path(settings.BASE_DIR) / "demo" / "media"
if _demo_media.is_dir() and not getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
    from whitenoise import WhiteNoise

    application = WhiteNoise(
        application,
        root=str(_demo_media),
        prefix="media/",
    )

# Vercel Python / деякі runtime очікують імʼя `app`.
app = application

if getattr(settings, "ENSURE_DEMO_SUPERUSER_ON_START", False):
    from src.core.demo_runtime import ensure_demo_superuser

    ensure_demo_superuser()
