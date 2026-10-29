"""Ensure demo superuser from DJANGO_SUPERUSER_* env vars."""

from django.core.management.base import BaseCommand, CommandError

from src.core.demo_runtime import ensure_demo_superuser


class Command(BaseCommand):
    help = (
        "Створює або оновлює суперкористувача з "
        "DJANGO_SUPERUSER_USERNAME / EMAIL / PASSWORD. "
        "На Vercel demo викликається на cold start, якщо змінні задані."
    )

    def handle(self, *args, **options):
        if not ensure_demo_superuser():
            raise CommandError(
                "Задайте DJANGO_SUPERUSER_USERNAME і DJANGO_SUPERUSER_PASSWORD."
            )
        self.stdout.write(self.style.SUCCESS("Demo superuser OK"))
