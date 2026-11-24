from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Campground(models.Model):
    class Registration(models.TextChoices):
        APPROVAL = "approval", "Administrator approval"
        OPEN = "open", "Open registration"
        INVITATION = "invitation", "Invitation only"
        DISABLED = "disabled", "Disabled"

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    name = models.CharField(max_length=120, default="Campground")
    welcome = models.TextField(max_length=3000, blank=True)
    rules = models.TextField(max_length=10000, blank=True)
    reservation_policy = models.TextField(max_length=10000, blank=True)
    policy_version = models.CharField(max_length=40, default="1")
    timezone = models.CharField(max_length=64, default="America/New_York")
    registration_mode = models.CharField(
        max_length=12, choices=Registration, default=Registration.APPROVAL
    )
    public_availability = models.BooleanField(default=False)
    min_nights = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    max_nights = models.PositiveSmallIntegerField(default=14, validators=[MaxValueValidator(90)])
    max_active = models.PositiveSmallIntegerField(
        default=2, validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    advance_days = models.PositiveSmallIntegerField(
        default=180, validators=[MaxValueValidator(730)]
    )
    notice_days = models.PositiveSmallIntegerField(default=1)
    cancellation_days = models.PositiveSmallIntegerField(default=2)
    modification_days = models.PositiveSmallIntegerField(default=2)
    allow_cancel = models.BooleanField(default=True)
    allow_modify = models.BooleanField(default=True)
    multiple_sites = models.BooleanField(default=False)
    approval_required = models.BooleanField(default=False)
    pending_hours = models.PositiveSmallIntegerField(
        default=24, validators=[MinValueValidator(1), MaxValueValidator(168)]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="campground_singleton"),
            models.CheckConstraint(
                condition=models.Q(
                    min_nights__gte=1, max_nights__lte=90, max_nights__gte=models.F("min_nights")
                ),
                name="policy_nights_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(max_active__gte=1, max_active__lte=20),
                name="policy_active_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    advance_days__lte=730, advance_days__gte=models.F("notice_days")
                ),
                name="policy_notice_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(pending_hours__gte=1, pending_hours__lte=168),
                name="policy_pending_valid",
            ),
        ]

    def clean(self):
        super().clean()
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValidationError({"timezone": "Select a valid IANA timezone."}) from None

    @classmethod
    def current(cls, *, lock=False):
        query = cls.objects.select_for_update() if lock else cls.objects
        return query.get(pk=1)
