from django.core.management.base import BaseCommand

from src.commerce.stock_hold import release_expired_holds


class Command(BaseCommand):
    help = "Повертає залишок карткових замовлень, у яких минув термін резерву."

    def handle(self, *args, **options):
        count = release_expired_holds()
        self.stdout.write(f"Повернуто резервів: {count}")
