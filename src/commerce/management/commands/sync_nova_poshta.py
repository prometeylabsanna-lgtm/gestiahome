import logging

from django.core.management.base import BaseCommand, CommandError

from src.commerce.novaposhta import NovaPoshtaError
from src.commerce.np_sync import sync_catalog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Завантажує повний каталог відділень Нової пошти."

    def handle(self, *args, **options):
        try:
            result = sync_catalog()
        except NovaPoshtaError as exc:
            logger.warning("sync_nova_poshta failed: %s", exc)
            raise CommandError(str(exc)) from exc
        if result["skipped"]:
            self.stdout.write(result["message"])
            return
        self.stdout.write(
            f"Синхронізовано відділень: {result['warehouses']}, міст: {result['cities']}"
        )
