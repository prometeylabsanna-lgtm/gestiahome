"""Українські підписи django-axes в адмінці. Міграцій axes не створює."""

from axes.apps import AppConfig as AxesAppConfig


class AxesUkConfig(AxesAppConfig):
    verbose_name = "Доступ"

    def ready(self):
        super().ready()
        self._apply_uk_labels()

    @staticmethod
    def _apply_uk_labels():
        from axes.models import (
            AccessAttempt,
            AccessAttemptExpiration,
            AccessFailureLog,
            AccessLog,
        )

        AccessAttempt._meta.verbose_name = "спроба входу"
        AccessAttempt._meta.verbose_name_plural = "Спроби входу"
        AccessFailureLog._meta.verbose_name = "невдалий вхід"
        AccessFailureLog._meta.verbose_name_plural = "Невдалі входи"
        AccessLog._meta.verbose_name = "журнал доступу"
        AccessLog._meta.verbose_name_plural = "Журнали доступу"
        AccessAttemptExpiration._meta.verbose_name = "термін спроби входу"
        AccessAttemptExpiration._meta.verbose_name_plural = "Терміни спроб входу"
