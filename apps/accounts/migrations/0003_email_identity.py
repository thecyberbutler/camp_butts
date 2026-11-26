"""Remove user-selected usernames without dropping account uniqueness or live lockouts."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import migrations, models
from django.utils import timezone

import apps.accounts.managers


def prepare_email_identity(apps, schema_editor):
    alias = schema_editor.connection.alias
    User = apps.get_model("accounts", "User")
    EmailAddress = apps.get_model("account", "EmailAddress")
    Attempt = apps.get_model("axes", "AccessAttempt")
    Expiration = apps.get_model("axes", "AccessAttemptExpiration")
    Session = apps.get_model("sessions", "Session")
    users = list(User.objects.using(alias).values("pk", "email", "username"))
    canonical = {}
    seen = set()
    for user in users:
        email = user["email"].strip().casefold()
        try:
            validate_email(email)
        except ValidationError:
            raise RuntimeError("Review invalid account email before migration.") from None
        if len(email) > 254 or email in seen:
            raise RuntimeError("Review colliding or oversized account email before migration.")
        seen.add(email)
        canonical[user["pk"]] = email
    for address in EmailAddress.objects.using(alias).values("user_id", "email"):
        if address["email"].strip().casefold() != canonical.get(address["user_id"]):
            raise RuntimeError("Review secondary or mismatched account email before migration.")

    now = timezone.now()
    # Preserve all original IP/account attempt rows. Carry recent legacy-identifier counts
    # into the new email identity; conservatively restart their existing 15-minute window.
    # Read counts before any inserts so one account's alias cannot influence the next.
    counts = {}
    for user in users:
        counts[user["pk"]] = (
            Attempt.objects.using(alias)
            .filter(
                username=user["username"].casefold(), attempt_time__gte=now - timedelta(minutes=15)
            )
            .aggregate(total=models.Sum("failures_since_start"))["total"]
            or 0
        )
    for user in users:
        email = canonical[user["pk"]]
        if counts[user["pk"]] and user["username"].casefold() != email:
            attempt, _ = Attempt.objects.using(alias).get_or_create(
                username=email,
                ip_address=None,
                user_agent="email-identity-migration",
                defaults={
                    "failures_since_start": 0,
                    "http_accept": "",
                    "path_info": "",
                    "get_data": "",
                    "post_data": "",
                },
            )
            Attempt.objects.using(alias).filter(pk=attempt.pk).update(
                failures_since_start=models.F("failures_since_start") + counts[user["pk"]],
                attempt_time=now,
            )
            Expiration.objects.using(alias).update_or_create(
                access_attempt_id=attempt.pk, defaults={"expires_at": now + timedelta(minutes=15)}
            )
        User.objects.using(alias).filter(pk=user["pk"]).update(
            email=email, security_version=models.F("security_version") + 1
        )
        EmailAddress.objects.using(alias).filter(user_id=user["pk"]).update(email=email)
    # Retire authenticated sessions and pending OAuth/MFA/signup state across the cutover.
    Session.objects.using(alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_alter_user_options"),
        ("account", "0009_emailaddress_unique_primary_email"),
        ("axes", "0010_accessattemptexpiration"),
        ("sessions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(prepare_email_identity),
        migrations.AlterModelManagers(
            name="user", managers=[("objects", apps.accounts.managers.UserManager())]
        ),
        migrations.RemoveConstraint(model_name="user", name="username_case_unique"),
        migrations.RemoveField(model_name="user", name="username"),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=~models.Q(email=""), name="email_not_empty"
            ),
        ),
    ]
