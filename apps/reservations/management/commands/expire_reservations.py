from django.core.management.base import BaseCommand

from apps.reservations.services import expire_pending


class Command(BaseCommand):
    help = "Expire pending holds atomically; safe to run concurrently and repeatedly."

    def handle(self, *args, **options):
        self.stdout.write(f"Expired {expire_pending()} pending reservations.")
