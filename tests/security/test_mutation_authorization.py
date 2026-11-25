import uuid
from datetime import timedelta

import pytest
from allauth.account.internal.flows.login import record_authentication
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.test import RequestFactory

from apps.accounts.middleware import security_stamp
from apps.accounts.models import User
from apps.accounts.security import lock_staff
from apps.configuration.models import Campground
from apps.dashboard.views import approve, change_status, maintenance
from apps.reservations.models import Occupancy

pytestmark = pytest.mark.django_db


def test_stale_privileged_request_cannot_mutate_after_revocation(staff):
    TOTP.activate(staff, generate_totp_secret())
    request = RequestFactory().post("/c/default/operations/maintenance/")
    SessionMiddleware(lambda _: None).process_request(request)
    request.user = staff
    request.session["security_stamp"] = security_stamp(staff)
    record_authentication(request, staff, "mfa", type="totp")
    # The object already held by the request is stale, as during concurrent change.
    User.objects.filter(pk=staff.pk).update(approved=False, security_version=2)
    with transaction.atomic(), pytest.raises(PermissionDenied):
        Campground.current(lock=True)
        lock_staff(request, "reservations.block_campsite")


@pytest.mark.parametrize("operation", ["approve", "status", "maintenance"])
def test_staff_views_recheck_session_after_waiting_for_policy_lock(
    staff, other, booking, site, dates, operation
):
    TOTP.activate(staff, generate_totp_secret())
    data = {
        "approve": {},
        "status": {"status": "cancelled"},
        "maintenance": {
            "campsite": site.pk,
            "start": dates[1],
            "end": dates[1] + timedelta(days=1),
            "reason": "Grounds work",
            "submission_key": uuid.uuid4(),
        },
    }[operation]
    request = RequestFactory().post("/c/default/operations/", data)
    SessionMiddleware(lambda _: None).process_request(request)
    request.user = staff
    request.session["security_stamp"] = security_stamp(staff)
    record_authentication(request, staff, "mfa", type="totp")
    # MFA/permission checks still succeed on the request's cached identity, but
    # a security change committed before the operation acquires its locks.
    User.objects.filter(pk=staff.pk).update(security_version=staff.security_version + 1)
    other.approved = False
    other.save(update_fields=["approved"])
    with pytest.raises(PermissionDenied):
        if operation == "approve":
            approve(request, other.pk)
        elif operation == "status":
            change_status(request, booking.pk)
        else:
            maintenance(request)
    other.refresh_from_db()
    booking.refresh_from_db()
    assert not other.approved
    assert booking.status == "confirmed"
    assert not Occupancy.objects.filter(kind="block").exists()
