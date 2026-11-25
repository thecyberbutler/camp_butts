import time

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.totp.internal.auth import TOTP, format_hotp_value, generate_totp_secret, hotp_value
from django.contrib.auth.models import Permission
from django.test import Client

from apps.audit.models import Event
from apps.campsites.models import Amenity, CampsiteType

pytestmark = pytest.mark.django_db


@pytest.fixture
def account_admin(staff, password):
    staff.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["manage_camper", "view_event", "add_campsitetype", "add_amenity"]
        )
    )
    secret = generate_totp_secret()
    TOTP.activate(staff, secret)
    EmailAddress.objects.create(user=staff, email=staff.email, primary=True, verified=True)
    client = Client()
    client.post(
        "/c/default/accounts/login/", {"login": staff.username, "password": password}, secure=True
    )
    code = format_hotp_value(hotp_value(secret, int(time.time()) // 30))
    client.post("/c/default/accounts/2fa/authenticate/", {"code": code}, secure=True)
    return client


def test_deactivation_and_reactivation_never_revive_a_session(account_admin, browser, camper):
    original_version = camper.security_version
    path = f"/c/default/operations/campers/{camper.pk}/state/"
    assert (
        account_admin.post(path, {"active": "false", "confirm": "on"}, secure=True).status_code
        == 302
    )
    camper.refresh_from_db()
    assert not camper.is_active
    # Do not send the old camper session while inactive: revocation must still be
    # effective if the next request happens only after account reactivation.
    assert (
        account_admin.post(
            path, {"active": "true", "confirm": "on", "is_staff": "true"}, secure=True
        ).status_code
        == 302
    )
    camper.refresh_from_db()
    assert camper.is_active and not camper.is_staff
    assert camper.security_version == original_version + 2
    assert browser.get("/c/default/dashboard/", secure=True).status_code == 302
    assert (
        Event.objects.filter(action="account.status_changed", object_id=str(camper.pk)).count() == 2
    )


def test_inactive_permission_holder_is_outside_camper_management(account_admin, other):
    other.user_permissions.add(Permission.objects.get(codename="view_event"))
    other.is_active = False
    other.save()
    assert (
        account_admin.post(
            f"/c/default/operations/campers/{other.pk}/state/",
            {"active": "true", "confirm": "on"},
            secure=True,
        ).status_code
        == 403
    )
    other.refresh_from_db()
    assert not other.is_active


def test_audit_and_classifications_are_permission_protected(account_admin, browser):
    assert browser.get("/c/default/operations/audit/", secure=True).status_code == 403
    assert account_admin.get("/c/default/operations/audit/", secure=True).status_code == 200
    assert Event.objects.filter(action="audit.viewed").exists()
    assert (
        account_admin.post(
            "/c/default/operations/site-types/new/", {"name": "Accessible cabin"}, secure=True
        ).status_code
        == 302
    )
    assert (
        account_admin.post(
            "/c/default/operations/amenities/new/", {"name": "Drinking water"}, secure=True
        ).status_code
        == 302
    )
    assert CampsiteType.objects.filter(name="Accessible cabin").exists()
    assert Amenity.objects.filter(name="Drinking water").exists()
    assert (
        browser.post(
            "/c/default/operations/amenities/new/", {"name": "Not authorized"}, secure=True
        ).status_code
        == 403
    )
