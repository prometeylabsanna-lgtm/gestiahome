from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.catalog"
    verbose_name = "Каталог"

    def ready(self):
        from django.db.backends.signals import connection_created

        from src.catalog.sqlite_fold import register_sqlite_fold

        connection_created.connect(register_sqlite_fold, dispatch_uid="catalog.py_fold")
