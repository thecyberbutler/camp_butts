"""Reservation policies and mutations. Lock order is policy, accounts, site, occupancy."""

import hashlib
import json
import uuid
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from psycopg.types.range import Range

from apps.accounts.models import User
from apps.audit.services import record
from apps.campsites.models import Campsite
from apps.configuration.models import Campground
from apps.notifications.models import Notification

from .models import ACTIVE, Occupancy


class BookingError(ValidationError):
    pass


def today(policy):
    return timezone.localdate(timezone=ZoneInfo(policy.timezone))


def date_range(start: date, end: date) -> Range:
    if type(start) is not date or type(end) is not date or not 0 < (end - start).days <= 90:
        raise BookingError("Choose a stay between 1 and 90 nights.")
    return Range(start, end, bounds="[)")


def eligible(user):
    if not user.is_authenticated or not user.is_active or not user.approved:
        raise PermissionDenied("An approved, active account is required.")
    if (
        settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory"
        and not EmailAddress.objects.filter(
            user=user, email__iexact=user.email, verified=True
        ).exists()
    ):
        raise PermissionDenied("Verify your email before booking.")


def lock_accounts(actor, camper_id):
    if not actor.is_authenticated:
        raise PermissionDenied
    users = {
        u.pk: u
        for u in User.objects.select_for_update()
        .filter(pk__in={actor.pk, camper_id})
        .order_by("pk")
    }
    if actor.pk not in users or camper_id not in users:
        raise PermissionDenied
    acting, camper = users[actor.pk], users[camper_id]
    eligible(acting)
    eligible(camper)
    if acting.pk != camper.pk and not acting.has_perm("reservations.operate_reservations"):
        raise PermissionDenied
    return acting, camper


def payload_fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def existing_submission(actor, key, fingerprint):
    if not isinstance(key, uuid.UUID):
        raise BookingError("Invalid submission identifier.")
    existing = Occupancy.objects.filter(created_by=actor, submission_key=key).first()
    if existing and existing.request_fingerprint != fingerprint:
        raise BookingError("This submission identifier has already been used. Reload the form.")
    return existing


def validate_policy(
    policy, camper, site, dates, *, adults, children, pets, rv_length, exclude=None
):
    local_today = today(policy)
    if not site.active:
        raise BookingError("This campsite is unavailable.")
    nights = (dates.upper - dates.lower).days
    if not policy.min_nights <= nights <= policy.max_nights:
        raise BookingError("The stay does not meet the campground's length policy.")
    notice = (dates.lower - local_today).days
    if not policy.notice_days <= notice <= policy.advance_days:
        raise BookingError("The stay is outside the booking window.")
    if any(type(n) is not int or n < 0 or n > 1000 for n in (adults, children, pets, rv_length)):
        raise BookingError("Invalid guest or vehicle count.")
    if adults < 1 or adults + children > site.max_occupancy:
        raise BookingError("The guest count exceeds campsite capacity.")
    if pets and not site.pets_allowed:
        raise BookingError("Pets are not permitted at this campsite.")
    if rv_length > site.max_rv_length:
        raise BookingError("The RV exceeds this campsite's capacity.")
    active = Occupancy.objects.filter(
        camper=camper, status__in=ACTIVE, dates__endswith__gt=local_today
    )
    if exclude:
        active = active.exclude(pk=exclude)
    if active.count() >= policy.max_active:
        raise BookingError("The active reservation limit has been reached.")
    if not policy.multiple_sites and active.filter(dates__overlap=dates).exists():
        raise BookingError("An existing reservation overlaps these dates.")
    occupied = Occupancy.objects.filter(campsite=site, status__in=ACTIVE, dates__overlap=dates)
    if exclude:
        occupied = occupied.exclude(pk=exclude)
    if occupied.exists():
        raise BookingError("The campsite is no longer available for these dates.")


def notify(occupancy, message):
    if occupancy.camper_id:
        # The notification row is invisible to other transactions until commit.
        Notification.objects.create(recipient=occupancy.camper, message=message)


def book(
    *,
    actor,
    campsite_id,
    start,
    end,
    submission_key,
    adults=1,
    children=0,
    pets=0,
    rv_length=0,
    notes="",
    camper_id=None,
):
    dates = date_range(start, end)
    if not isinstance(notes, str) or len(notes) > 2000:
        raise BookingError("Notes must be at most 2000 characters.")
    camper_id = camper_id or actor.pk
    fingerprint = payload_fingerprint(
        {
            "site": campsite_id,
            "camper": camper_id,
            "start": start,
            "end": end,
            "adults": adults,
            "children": children,
            "pets": pets,
            "rv": rv_length,
            "notes": notes,
        }
    )
    try:
        with transaction.atomic():
            policy = Campground.current(lock=True)
            actor, camper = lock_accounts(actor, camper_id)
            existing = existing_submission(actor, submission_key, fingerprint)
            if existing:
                return existing
            site = Campsite.objects.select_for_update().get(pk=campsite_id)
            validate_policy(
                policy,
                camper,
                site,
                dates,
                adults=adults,
                children=children,
                pets=pets,
                rv_length=rv_length,
            )
            item = Occupancy.objects.create(
                campsite=site,
                camper=camper,
                dates=dates,
                adults=adults,
                children=children,
                pets=pets,
                rv_length=rv_length,
                camper_notes=notes,
                status="pending" if policy.approval_required else "confirmed",
                expires_at=timezone.now() + timedelta(hours=policy.pending_hours)
                if policy.approval_required
                else None,
                submission_key=submission_key,
                request_fingerprint=fingerprint,
                created_by=actor,
                modified_by=actor,
            )
            record(actor=actor, action="reservation.created", obj=item, current=item.status)
            notify(item, "Your reservation has been created. Visit your dashboard for details.")
            return item
    except IntegrityError:
        raise BookingError(
            "The reservation could not be completed. Refresh availability."
        ) from None


def available(
    *, start, end, adults=1, site_type=None, amenities=(), rv_length=0, pets=False, electric_amps=0
):
    dates = date_range(start, end)
    sites = Campsite.objects.filter(
        active=True,
        max_occupancy__gte=adults,
        max_rv_length__gte=rv_length,
        electric_amps__gte=electric_amps,
    )
    if site_type:
        sites = sites.filter(site_type=site_type)
    if pets:
        sites = sites.filter(pets_allowed=True)
    for amenity in amenities:
        sites = sites.filter(amenities=amenity)
    busy = Occupancy.objects.filter(status__in=ACTIVE, dates__overlap=dates).values("campsite_id")
    return sites.exclude(pk__in=busy).select_related("site_type")


def owned_query(actor):
    if not actor.is_authenticated:
        raise PermissionDenied
    return Occupancy.objects.filter(camper=actor, kind="reservation").select_related("campsite")


def cancel(*, actor, reservation_id, reason=""):
    if not isinstance(reason, str) or len(reason) > 500:
        raise BookingError("Cancellation reason must be at most 500 characters.")
    with transaction.atomic():
        policy = Campground.current(lock=True)
        # Filter ownership before locking or returning any record.
        item = owned_query(actor).get(pk=reservation_id)
        actor, _ = lock_accounts(actor, actor.pk)
        Campsite.objects.select_for_update().get(pk=item.campsite_id)
        item = Occupancy.objects.select_for_update().get(pk=item.pk)
        if item.status == "cancelled":
            return item
        if item.status not in ("pending", "confirmed") or not policy.allow_cancel:
            raise BookingError("This reservation cannot be cancelled.")
        if (item.check_in - today(policy)).days < policy.cancellation_days:
            raise BookingError("The cancellation deadline has passed. Contact campground staff.")
        previous = item.status
        item.status, item.reason, item.cancelled_at = "cancelled", reason, timezone.now()
        item.modified_by = actor
        item.save(update_fields=["status", "reason", "cancelled_at", "modified_by", "updated_at"])
        record(
            actor=actor,
            action="reservation.cancelled",
            obj=item,
            previous=previous,
            current=item.status,
        )
        notify(item, "Your reservation has been cancelled.")
        return item


def modify(*, actor, reservation_id, start, end):
    dates = date_range(start, end)
    try:
        with transaction.atomic():
            policy = Campground.current(lock=True)
            item = owned_query(actor).get(pk=reservation_id)
            actor, camper = lock_accounts(actor, actor.pk)
            site = Campsite.objects.select_for_update().get(pk=item.campsite_id)
            item = Occupancy.objects.select_for_update().get(pk=item.pk)
            if not policy.allow_modify or item.status not in ("pending", "confirmed"):
                raise BookingError("This reservation cannot be modified.")
            if (item.check_in - today(policy)).days < policy.modification_days:
                raise BookingError("The modification deadline has passed.")
            validate_policy(
                policy,
                camper,
                site,
                dates,
                adults=item.adults,
                children=item.children,
                pets=item.pets,
                rv_length=item.rv_length,
                exclude=item.pk,
            )
            item.dates, item.modified_by = dates, actor
            item.save(update_fields=["dates", "modified_by", "updated_at"])
            record(actor=actor, action="reservation.modified", obj=item)
            notify(item, "Your reservation dates have changed.")
            return item
    except IntegrityError:
        raise BookingError("The changed dates are unavailable.") from None


def block(*, actor, campsite_id, start, end, reason, submission_key):
    dates = date_range(start, end)
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise BookingError("Provide a maintenance reason of at most 500 characters.")
    fingerprint = payload_fingerprint(
        {"kind": "block", "site": campsite_id, "start": start, "end": end, "reason": reason}
    )
    try:
        with transaction.atomic():
            Campground.current(lock=True)
            actor, _ = lock_accounts(actor, actor.pk)
            if not actor.has_perm("reservations.block_campsite"):
                raise PermissionDenied
            existing = existing_submission(actor, submission_key, fingerprint)
            if existing:
                return existing
            site = Campsite.objects.select_for_update().get(pk=campsite_id)
            item = Occupancy.objects.create(
                campsite=site,
                kind="block",
                dates=dates,
                reason=reason,
                submission_key=submission_key,
                request_fingerprint=fingerprint,
                created_by=actor,
                modified_by=actor,
            )
            record(actor=actor, action="campsite.blocked", obj=item)
            return item
    except IntegrityError:
        raise BookingError(
            "The proposed maintenance block conflicts with occupied dates."
        ) from None


TRANSITIONS = {
    "pending": {"confirmed", "rejected", "cancelled"},
    "confirmed": {"checked_in", "cancelled", "no_show"},
    "checked_in": {"checked_out"},
}


def transition(*, actor, reservation_id, status):
    with transaction.atomic():
        policy = Campground.current(lock=True)
        actor, _ = lock_accounts(actor, actor.pk)
        if not actor.has_perm("reservations.operate_reservations"):
            raise PermissionDenied
        item = Occupancy.objects.select_for_update().get(pk=reservation_id, kind="reservation")
        if status not in TRANSITIONS.get(item.status, set()):
            raise BookingError("Invalid reservation status transition.")
        if item.status == "pending" and item.expires_at <= timezone.now():
            raise BookingError("This pending reservation has expired.")
        local_today = today(policy)
        if status == "checked_in" and not item.check_in <= local_today < item.check_out:
            raise BookingError("Check-in must occur during the reserved stay.")
        if status == "no_show" and local_today < item.check_in:
            raise BookingError("A future arrival cannot be marked as a no-show.")
        previous, item.status, item.modified_by = item.status, status, actor
        if status == "cancelled":
            item.cancelled_at = timezone.now()
        item.save(update_fields=["status", "modified_by", "cancelled_at", "updated_at"])
        record(
            actor=actor,
            action="reservation.transitioned",
            obj=item,
            previous=previous,
            current=status,
        )
        notify(item, f"Your reservation status is now {item.get_status_display()}.")
        return item


def expire_pending():
    with transaction.atomic():
        Campground.current(lock=True)
        rows = Occupancy.objects.select_for_update().filter(
            status="pending", expires_at__lte=timezone.now()
        )
        count = 0
        for item in rows:
            item.status = "rejected"
            item.save(update_fields=["status", "updated_at"])
            record(
                actor=None,
                action="reservation.expired",
                obj=item,
                previous="pending",
                current="rejected",
            )
            notify(item, "Your pending reservation has expired and its inventory was released.")
            count += 1
        return count
