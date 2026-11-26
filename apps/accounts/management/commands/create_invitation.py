import hashlib
import os
import secrets
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Invitation, User
from apps.audit.services import record


class Command(BaseCommand):
    help = (
        "Create a bounded invitation; write its secret once to a new protected file, never stdout."
    )

    def add_arguments(self, parser):
        parser.add_argument("--actor", required=True, help="Account email address")
        parser.add_argument("--output", type=Path, required=True)
        parser.add_argument("--uses", type=int, default=1)
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **options):
        if not 1 <= options["uses"] <= 100 or not 1 <= options["days"] <= 30:
            raise CommandError("Use limits 1–100 and expiry 1–30 days are required.")
        user = User.objects.get(email__iexact=options["actor"], is_active=True, approved=True)
        if not user.has_perm("accounts.approve_camper"):
            raise CommandError("Actor lacks account administration permission.")
        path = options["output"]
        if path.parent.is_symlink() or path.parent.stat().st_mode & 0o077:
            raise CommandError("Output must be in a protected 0700 directory.")
        token = secrets.token_urlsafe(32)
        try:
            with transaction.atomic():
                item = Invitation.objects.create(
                    digest=hashlib.sha256(token.encode()).hexdigest(),
                    expires_at=timezone.now() + timedelta(days=options["days"]),
                    max_uses=options["uses"],
                    created_by=user,
                )
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "w") as stream:
                    stream.write(token)
                record(actor=user, action="invitation.created", obj=item)
        except OSError:
            raise CommandError("Could not create protected invitation file.") from None
        self.stdout.write(
            "Invitation created in the requested protected file; value not displayed."
        )
