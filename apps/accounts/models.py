import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    approved = models.BooleanField(default=False)
    security_version = models.PositiveIntegerField(default=1)
    policy_version = models.CharField(max_length=40, blank=True)
    policy_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("username"), name="username_case_unique"),
            models.UniqueConstraint(Lower("email"), name="email_case_unique"),
        ]
        permissions = [
            ("approve_camper", "Approve camper accounts"),
            ("manage_camper", "Deactivate and reactivate non-privileged camper accounts"),
        ]


class Invitation(models.Model):
    digest = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    uses = models.PositiveIntegerField(default=0)
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_uses__gte=1), name="invite_positive_limit"
            ),
            models.CheckConstraint(
                condition=models.Q(uses__lte=models.F("max_uses")), name="invite_usage_limit"
            ),
        ]
