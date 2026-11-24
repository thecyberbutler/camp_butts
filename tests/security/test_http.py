import pytest
from django.test import Client

from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


def test_csrf_and_no_get_mutation(browser, booking):
    path = f"/reservations/{booking.pk}/cancel/"
    assert browser.get(path, secure=True).status_code == 200
    booking.refresh_from_db()
    assert booking.status == "confirmed"
    assert browser.post(path, {"confirm": "on"}, secure=True).status_code == 403


def test_idor_standard_and_htmx(other, booking):
    client = Client()
    client.force_login(other, backend="allauth.account.auth_backends.AuthenticationBackend")
    for suffix in ("", "cancel/", "modify/"):
        for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
            assert (
                client.get(
                    f"/reservations/{booking.pk}/{suffix}", secure=True, **headers
                ).status_code
                == 404
            )


def test_private_notes_and_xss(browser, booking):
    booking.staff_notes = "PRIVATE STAFF INFORMATION"
    booking.camper_notes = "<script>alert(1)</script>"
    booking.save()
    response = browser.get(f"/reservations/{booking.pk}/", secure=True)
    assert b"PRIVATE STAFF INFORMATION" not in response.content
    assert b"<script>alert" not in response.content
    assert b"&lt;script&gt;" in response.content
    assert response["Cache-Control"] == "no-store, private"
    assert "unsafe-inline" not in response["Content-Security-Policy"]
    assert "unsafe-eval" not in response["Content-Security-Policy"]


def test_notification_owner_only(browser, other):
    item = Notification.objects.create(recipient=other, message="Private")
    assert b"Private" not in browser.get("/notifications/", secure=True).content
    client = Client()
    from apps.accounts.models import User

    user = User.objects.get(pk=browser.session["_auth_user_id"])
    client.force_login(user, backend="allauth.account.auth_backends.AuthenticationBackend")
    assert client.post(f"/notifications/{item.pk}/read/", secure=True).status_code == 404


def test_https_host_and_forwarded_header(client):
    assert (
        client.get("/", HTTP_X_FORWARDED_PROTO="https", HTTP_X_REAL_IP="192.0.2.1").status_code
        == 301
    )
    assert client.get("/", secure=True, HTTP_HOST="evil.invalid").status_code == 400


def test_pending_cannot_book(browser, camper, site):
    camper.approved = False
    camper.save()
    # Revokes the existing session immediately.
    assert browser.get(f"/campsites/{site.pk}/reserve/", secure=True).status_code == 302


def test_privileged_password_only_session_denied(staff):
    client = Client()
    client.force_login(staff, backend="allauth.account.auth_backends.AuthenticationBackend")
    assert client.get("/dashboard/", secure=True).status_code == 403
    assert client.get("/accounts/2fa/", secure=True).status_code == 200
    assert client.get("/admin/", secure=True).status_code == 404


def test_role_change_invalidates_existing_session(browser, camper):
    camper.is_staff = True
    camper.save()
    assert browser.get("/dashboard/", secure=True).status_code == 302


def test_idle_and_absolute_expiry(browser):
    session = browser.session
    session["authenticated_at"] = 1
    session.save()
    assert browser.get("/dashboard/", secure=True).status_code == 302


def test_smtp_unavailable_has_no_recovery_fallback(client):
    assert client.get("/accounts/password/reset/", secure=True).status_code == 403
