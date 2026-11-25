import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection

from apps.configuration.importing import import_profile


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate field")
        result[key] = value
    return result


class Command(BaseCommand):
    help = "Import reviewed public information into an empty inactive campground; never fetch URLs."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, required=True)

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user")
            role = cursor.fetchone()[0]
        testing = settings.SETTINGS_MODULE == "config.settings.testing"
        if role != "campground_migrator" and not (testing and role == "campground_test_runner"):
            raise CommandError("Import requires the protected migration identity.")
        path = options["file"]
        try:
            if path.is_symlink() or not path.is_file() or path.suffix != ".json":
                raise ValueError("Regular JSON file required")
            with path.open("rb") as stream:
                raw = stream.read(262145)
            if len(raw) > 262144:
                raise ValueError("Import is too large")
            profile = json.loads(raw, object_pairs_hook=unique_keys)
            changed = import_profile(profile)
        except (OSError, ValueError, TypeError, KeyError, ValidationError, DatabaseError):
            raise CommandError(
                "Import refused. Check the profile, tenant state and existing data; values omitted."
            ) from None
        self.stdout.write(
            "Campground profile imported as inactive drafts."
            if changed
            else "Identical profile already imported; existing data preserved."
        )
