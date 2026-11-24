import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.campsites.models import Amenity, Campsite, CampsiteType


class Command(BaseCommand):
    help = "Seed 30 synthetic campsites; no reusable account passwords."

    @transaction.atomic
    def handle(self, *args, **options):
        if os.environ.get("DJANGO_SETTINGS_MODULE") not in {
            "config.settings.development",
            "config.settings.testing",
        }:
            raise CommandError("Demo seeding is forbidden outside isolated development/testing.")
        kinds = [
            CampsiteType.objects.get_or_create(name=name)[0] for name in ("Tent", "RV", "Cabin")
        ]
        amenities = [
            Amenity.objects.get_or_create(name=name)[0]
            for name in ("Fire ring", "Picnic table", "Shade")
        ]
        for n in range(30):
            site, _ = Campsite.objects.get_or_create(
                name=f"Demo {n + 1:02}",
                defaults={
                    "site_type": kinds[n % 3],
                    "description": "Synthetic development campsite.",
                    "max_occupancy": 6,
                    "max_rv_length": 40 if n % 3 == 1 else 0,
                    "pets_allowed": True,
                    "display_order": n,
                    "map_x": 60 + n % 6 * 150,
                    "map_y": 60 + n // 6 * 150,
                },
            )
            site.amenities.set(amenities)
        self.stdout.write("Seeded 30 synthetic campsites. No login credentials created.")
