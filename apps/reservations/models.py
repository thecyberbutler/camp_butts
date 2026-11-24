import uuid

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.db import models


class BoundedDateRange(models.Func):
    output_field = models.BooleanField()
    template = (
        "(NOT isempty(%(expressions)s) AND NOT lower_inf(%(expressions)s) "
        "AND NOT upper_inf(%(expressions)s) AND isfinite(lower(%(expressio"
        "ns)s)) AND isfinite(upper(%(expressions)s)))"
    )


class Occupancy(models.Model):
    class Kind(models.TextChoices):
        RESERVATION = "reservation", "Reservation"
        BLOCK = "block", "Maintenance block"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending approval"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked in"
        CHECKED_OUT = "checked_out", "Checked out"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"
        NO_SHOW = "no_show", "No-show"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campsite = models.ForeignKey("campsites.Campsite", on_delete=models.PROTECT)
    camper = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="reservations"
    )
    kind = models.CharField(max_length=12, choices=Kind, default=Kind.RESERVATION)
    dates = DateRangeField()
    status = models.CharField(max_length=12, choices=Status, default=Status.CONFIRMED)
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    pets = models.PositiveSmallIntegerField(default=0)
    rv_length = models.PositiveSmallIntegerField(default=0)
    camper_notes = models.TextField(max_length=2000, blank=True)
    staff_notes = models.TextField(max_length=2000, blank=True)
    reason = models.CharField(max_length=500, blank=True)
    submission_key = models.UUIDField()
    request_fingerprint = models.CharField(max_length=64)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_occupancies"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="modified_occupancies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("operate_reservations", "Operate campground reservations"),
            ("block_campsite", "Create maintenance blocks"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=BoundedDateRange("dates"), name="occupancy_bounded_nonempty"
            ),
            models.CheckConstraint(
                condition=models.Q(kind="reservation", camper__isnull=False, adults__gte=1)
                | models.Q(kind="block", camper__isnull=True),
                name="occupancy_kind_owner",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "pending",
                        "confirmed",
                        "checked_in",
                        "checked_out",
                        "cancelled",
                        "rejected",
                        "no_show",
                    ]
                ),
                name="occupancy_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(status="pending") | models.Q(expires_at__isnull=False),
                name="pending_expiry_required",
            ),
            models.UniqueConstraint(
                fields=["created_by", "submission_key"], name="occupancy_idempotency"
            ),
            ExclusionConstraint(
                name="no_overlapping_occupancy",
                expressions=[
                    ("campsite", RangeOperators.EQUAL),
                    ("dates", RangeOperators.OVERLAPS),
                ],
                condition=models.Q(status__in=["pending", "confirmed", "checked_in"]),
            ),
        ]

    @property
    def confirmation(self):
        return str(self.id).upper()

    @property
    def check_in(self):
        return self.dates.lower

    @property
    def check_out(self):
        return self.dates.upper


ACTIVE = (Occupancy.Status.PENDING, Occupancy.Status.CONFIRMED, Occupancy.Status.CHECKED_IN)
