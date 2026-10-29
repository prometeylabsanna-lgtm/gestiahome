from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.core"
    verbose_name = "Спільне"

    def ready(self):
        from src.core import admin_log  # noqa: F401
        from src.core.images import connect as connect_images
        from src.core.richtext import connect as connect_richtext

        connect_richtext()
        connect_images()
