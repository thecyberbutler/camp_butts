from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Create explicit least-privileged operational groups after migrations."

    @transaction.atomic
    def handle(self, *args, **options):
        assignments = {
            "Camper": [],
            "Staff": ["reservations.operate_reservations", "reservations.block_campsite"],
            "Administrator": [
                "reservations.operate_reservations",
                "reservations.block_campsite",
                "reservations.view_occupancy",
                "accounts.approve_camper",
                "campsites.add_campsite",
                "campsites.change_campsite",
                "configuration.change_campground",
                "audit.view_event",
            ],
        }
        for name, labels in assignments.items():
            group, _ = Group.objects.get_or_create(name=name)
            permissions = []
            for label in labels:
                app, codename = label.split(".")
                permissions.append(
                    Permission.objects.get(content_type__app_label=app, codename=codename)
                )
            group.permissions.set(permissions)
        self.stdout.write("Explicit role permissions initialized; no users or credentials created.")
