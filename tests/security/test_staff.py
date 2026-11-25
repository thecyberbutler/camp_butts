import time

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.totp.internal.auth import TOTP, format_hotp_value, generate_totp_secret, hotp_value
from django.test import Client

from apps.dashboard.views import safe_csv

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_browser(staff, password):
    secret = generate_totp_secret()
    TOTP.activate(staff, secret)
    EmailAddress.objects.create(user=staff, email=staff.email, verified=True, primary=True)
    client = Client()
    client.post(
        "/c/default/accounts/login/", {"login": staff.username, "password": password}, secure=True
    )
    code = format_hotp_value(hotp_value(secret, int(time.time()) // 30))
    client.post("/c/default/accounts/2fa/authenticate/", {"code": code}, secure=True)
    return client


@pytest.mark.parametrize(
    "path",
    [
        "/c/default/operations/",
        "/c/default/operations/maintenance/",
        "/c/default/operations/accounts/",
        "/c/default/operations/configuration/",
        "/c/default/operations/calendar/",
        "/c/default/operations/export/",
    ],
)
def test_camper_cannot_access_operations(browser, path):
    assert browser.get(path, secure=True).status_code == 403


def test_staff_operational_permissions_are_granular(staff_browser):
    assert staff_browser.get("/c/default/operations/", secure=True).status_code == 200
    assert staff_browser.get("/c/default/operations/calendar/", secure=True).status_code == 200
    assert staff_browser.get("/c/default/operations/configuration/", secure=True).status_code == 403
    assert staff_browser.get("/c/default/operations/export/", secure=True).status_code == 403


@pytest.mark.parametrize(
    "value", ["=HYPERLINK(1)", "+CMD", "-1", "@SUM(1)", "  =1", "\t=1", "\r=1"]
)
def test_csv_formula_sanitization(value):
    assert safe_csv(value).startswith("'")


def test_staff_approval_does_not_verify_email(staff_browser, other):
    other.approved = False
    other.save()
    assert (
        staff_browser.post(
            f"/c/default/operations/accounts/{other.pk}/approve/", secure=True
        ).status_code
        == 302
    )
    other.refresh_from_db()
    assert other.approved
    assert not EmailAddress.objects.filter(user=other, verified=True).exists()


def test_staff_status_and_maintenance_workflows(staff_browser, booking, site, dates):
    import uuid
    from datetime import timedelta

    from apps.reservations.models import Occupancy

    response = staff_browser.post(
        f"/c/default/operations/reservations/{booking.pk}/status/",
        {"status": "checked_out"},
        secure=True,
    )
    assert response.status_code == 200
    booking.refresh_from_db()
    assert booking.status == "confirmed"
    response = staff_browser.post(
        f"/c/default/operations/reservations/{booking.pk}/status/",
        {"status": "cancelled"},
        secure=True,
    )
    assert response.status_code == 302
    response = staff_browser.post(
        "/c/default/operations/maintenance/",
        {
            "campsite": site.pk,
            "start": dates[0],
            "end": dates[1],
            "reason": "Repairs",
            "submission_key": uuid.uuid4(),
        },
        secure=True,
    )
    assert response.status_code == 302
    assert Occupancy.objects.filter(kind="block").count() == 1
    response = staff_browser.get(
        "/c/default/operations/calendar/", {"start": dates[0], "end": dates[1]}, secure=True
    )
    assert b"Maintenance block" in response.content
    response = staff_browser.get(
        "/c/default/operations/calendar/",
        {"start": dates[0], "end": dates[1] + timedelta(days=40)},
        secure=True,
    )
    assert b"at most 31 days" in response.content


def test_admin_configuration_and_export_require_distinct_permissions(staff, password, site, dates):
    from django.contrib.auth.models import Permission

    from apps.audit.models import Event
    from apps.configuration.models import Campground

    staff.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["change_campground", "change_campsite", "view_occupancy"]
        )
    )
    secret = generate_totp_secret()
    TOTP.activate(staff, secret)
    EmailAddress.objects.create(user=staff, email=staff.email, verified=True, primary=True)
    client = Client()
    client.post(
        "/c/default/accounts/login/", {"login": staff.username, "password": password}, secure=True
    )
    client.post(
        "/c/default/accounts/2fa/authenticate/",
        {"code": format_hotp_value(hotp_value(secret, int(time.time()) // 30))},
        secure=True,
    )
    assert client.get("/c/default/operations/configuration/", secure=True).status_code == 200
    policy = Campground.current()
    from apps.dashboard.forms import PolicyForm

    data = {name: getattr(policy, name) for name in PolicyForm.Meta.fields}
    data["max_nights"] = 0
    assert client.post("/c/default/operations/configuration/", data, secure=True).status_code == 200
    policy.refresh_from_db()
    assert policy.max_nights == 14
    data["max_nights"] = 10
    assert client.post("/c/default/operations/configuration/", data, secure=True).status_code == 302
    assert Event.objects.filter(action="configuration.updated").exists()
    assert client.get(f"/c/default/operations/campsites/{site.pk}/", secure=True).status_code == 200
    response = client.get(
        "/c/default/operations/export/", {"start": dates[0], "end": dates[1]}, secure=True
    )
    assert response["Content-Type"].startswith("text/csv")
    assert Event.objects.filter(action="report.exported").exists()
