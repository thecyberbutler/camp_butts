from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record
from apps.configuration.models import Campground


class Command(BaseCommand):
    help = (
        "Protected host-operator workflow for approval/role assignment and"
        " verified email attestation."
    )

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument(
            "--role", choices=["Camper", "Staff", "Administrator"], default="Camper"
        )
        parser.add_argument("--attest-identity-checked", action="store_true", required=True)
        parser.add_argument("--attest-email-ownership-verified", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["attest_identity_checked"]:
            raise CommandError("Independent identity verification required.")
        Campground.current(lock=True)
        try:
            user = User.objects.select_for_update().get(email__iexact=options["email"])
        except User.DoesNotExist:
            raise CommandError("Account not found.") from None
        if user.is_superuser:
            raise CommandError("This workflow cannot alter superusers.")
        user.groups.set([Group.objects.get(name=options["role"])])
        user.is_staff = options["role"] != "Camper"
        user.approved = True
        user.security_version += 1
        user.save(update_fields=["is_staff", "approved", "security_version"])
        record(actor=None, action="operator.account_authorized", obj=user)
        if options["attest_email_ownership_verified"]:
            EmailAddress.objects.update_or_create(
                user=user, email=user.email, defaults={"primary": True, "verified": True}
            )
            record(actor=None, action="operator.email_ownership_attested", obj=user)
        self.stdout.write(
            "Account authorization recorded. "
            "Privileged access still requires MFA enrollment and login."
        )
