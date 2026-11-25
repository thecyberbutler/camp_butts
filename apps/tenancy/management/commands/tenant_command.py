import argparse

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.tenancy.context import lookup, tenant_scope


class Command(BaseCommand):
    help = "Run a reviewed management command inside an explicitly selected campground."

    def add_arguments(self, parser):
        parser.add_argument("--campground", required=True)
        parser.add_argument(
            "command",
            choices=[
                "migrate",
                "makemigrations",
                "setup_roles",
                "import_campground",
                "authorize_account",
                "create_invitation",
                "expire_reservations",
                "seed_demo_data",
                "clearsessions",
                "changepassword",
            ],
        )
        parser.add_argument("arguments", nargs=argparse.REMAINDER)

    def handle(self, *args, **options):
        tenant = lookup(options["campground"], include_inactive=True)
        if not tenant:
            raise CommandError("Unknown campground.")
        with tenant_scope(tenant):
            call_command(
                options["command"], *options["arguments"], stdout=self.stdout, stderr=self.stderr
            )
