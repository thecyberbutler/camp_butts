import uuid
from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from psycopg.types.range import Range

from apps.audit.models import Event
from apps.notifications.models import Notification
from apps.reservations.models import Occupancy
from apps.reservations.services import (
    BookingError,
    available,
    block,
    book,
    cancel,
    expire_pending,
    modify,
    transition,
)

pytestmark = pytest.mark.django_db


def make(camper, site, dates, **kwargs):
    return book(
        actor=camper,
        campsite_id=site.pk,
        start=dates[0],
        end=dates[1],
        submission_key=kwargs.pop("submission_key", uuid.uuid4()),
        **kwargs,
    )


def test_booking_cancellation_releases_inventory(camper, site, dates):
    item = make(camper, site, dates)
    assert not available(start=dates[0], end=dates[1]).exists()
    assert Notification.objects.filter(recipient=camper).count() == 1
    assert Event.objects.filter(action="reservation.created").count() == 1
    cancel(actor=camper, reservation_id=item.pk)
    assert available(start=dates[0], end=dates[1]).exists()
    assert cancel(actor=camper, reservation_id=item.pk).status == "cancelled"
    assert Notification.objects.filter(recipient=camper).count() == 2


def test_overlap_and_adjacent(booking, other, site, dates):
    with pytest.raises(BookingError):
        make(other, site, dates)
    adjacent = make(other, site, (dates[1], dates[1] + timedelta(days=2)))
    assert adjacent.check_in == booking.check_out


@pytest.mark.parametrize(
    "changes",
    [{"adults": 0}, {"adults": 7}, {"children": -1}, {"rv_length": 41}, {"notes": "x" * 2001}],
)
def test_server_policy_validation(camper, site, dates, changes):
    with pytest.raises(BookingError):
        make(camper, site, dates, **changes)
    assert not Occupancy.objects.exists()


def test_denied_account_and_staff_block_permission(camper, site, dates):
    with pytest.raises(PermissionDenied):
        block(
            actor=camper,
            campsite_id=site.pk,
            start=dates[0],
            end=dates[1],
            reason="Maintenance",
            submission_key=uuid.uuid4(),
        )
    camper.approved = False
    camper.save()
    with pytest.raises(PermissionDenied):
        make(camper, site, dates)


def test_block_excludes_reservation(staff, camper, site, dates):
    block(
        actor=staff,
        campsite_id=site.pk,
        start=dates[0],
        end=dates[1],
        reason="Maintenance",
        submission_key=uuid.uuid4(),
    )
    with pytest.raises(BookingError):
        make(camper, site, dates)


def test_reservation_rejects_block(booking, staff, site, dates):
    with pytest.raises(BookingError):
        block(
            actor=staff,
            campsite_id=site.pk,
            start=dates[0],
            end=dates[1],
            reason="Maintenance",
            submission_key=uuid.uuid4(),
        )
    assert Occupancy.objects.count() == 1


def test_idempotency_and_payload_binding(camper, site, dates):
    key = uuid.uuid4()
    first = make(camper, site, dates, submission_key=key)
    assert make(camper, site, dates, submission_key=key).pk == first.pk
    assert Notification.objects.count() == 1
    with pytest.raises(BookingError):
        make(camper, site, dates, submission_key=key, adults=2)


def test_modify_ownership_and_conflict(booking, other, site, dates):
    with pytest.raises(Occupancy.DoesNotExist):
        modify(actor=other, reservation_id=booking.pk, start=dates[0], end=dates[1])
    future = (dates[1] + timedelta(days=2), dates[1] + timedelta(days=4))
    make(other, site, future)
    with pytest.raises(BookingError):
        modify(actor=booking.camper, reservation_id=booking.pk, start=future[0], end=future[1])
    booking.refresh_from_db()
    assert booking.check_in == dates[0]


def test_pending_expiration_is_idempotent(policy, camper, site, dates):
    from django.utils import timezone

    policy.approval_required = True
    policy.save()
    item = make(camper, site, dates)
    assert item.status == "pending"
    Occupancy.objects.filter(pk=item.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert expire_pending() == 1
    assert expire_pending() == 0
    assert available(start=dates[0], end=dates[1]).exists()


def test_transition_rules(booking, staff, camper):
    with pytest.raises(PermissionDenied):
        transition(actor=camper, reservation_id=booking.pk, status="cancelled")
    with pytest.raises(BookingError):
        transition(actor=staff, reservation_id=booking.pk, status="checked_out")
    with pytest.raises(BookingError):
        transition(actor=staff, reservation_id=booking.pk, status="checked_in")
    assert (
        transition(actor=staff, reservation_id=booking.pk, status="cancelled").status == "cancelled"
    )


@pytest.mark.parametrize(
    "dates",
    [Range(None, None), Range(empty=True), Range(None, "2030-01-01"), Range("2030-01-01", None)],
)
def test_database_rejects_invalid_ranges(camper, site, dates):
    with pytest.raises(IntegrityError), transaction.atomic():
        Occupancy.objects.create(
            campsite=site,
            camper=camper,
            dates=dates,
            created_by=camper,
            modified_by=camper,
            submission_key=uuid.uuid4(),
            request_fingerprint="0" * 64,
        )


def test_database_direct_overlap_cannot_bypass_service(booking, other, site, dates):
    with pytest.raises(IntegrityError), transaction.atomic():
        Occupancy.objects.create(
            campsite=site,
            camper=other,
            dates=Range(*dates),
            created_by=other,
            modified_by=other,
            submission_key=uuid.uuid4(),
            request_fingerprint="0" * 64,
        )


def test_audit_failure_rolls_back_booking(camper, site, dates, monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("Audit unavailable")

    monkeypatch.setattr("apps.reservations.services.record", fail)
    with pytest.raises(RuntimeError):
        make(camper, site, dates)
    assert not Occupancy.objects.exists()
    assert not Notification.objects.exists()
