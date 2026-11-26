import re
import uuid
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client

from apps.accounts.models import User
from apps.campsites.models import Campsite
from apps.reservations.models import Occupancy

pytestmark = pytest.mark.django_db


def test_full_camper_workflow_with_csrf(browser, camper, site, dates):
    browser.defaults["HTTP_ORIGIN"] = "https://testserver"
    response = browser.get(f"/c/default/campsites/{site.pk}/reserve/", secure=True)
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())[1]
    form = {
        "csrfmiddlewaretoken": token,
        "start": dates[0],
        "end": dates[1],
        "adults": 2,
        "children": 0,
        "pets": 0,
        "rv_length": 0,
        "notes": "Looking forward to our stay",
        "submission_key": uuid.uuid4(),
    }
    response = browser.post(f"/c/default/campsites/{site.pk}/reserve/", form, secure=True)
    assert response.status_code == 302
    item = Occupancy.objects.get(camper=camper)
    assert browser.get(response.url, secure=True).status_code == 200
    search = {"start": dates[0], "end": dates[1], "adults": 1, "rv_length": 0, "electric_amps": 0}
    response = browser.get("/c/default/campsites/", search, secure=True, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert site.name.encode() not in response.content
    response = browser.post(
        f"/c/default/reservations/{item.pk}/modify/",
        {
            "csrfmiddlewaretoken": token,
            "start": dates[0] + timedelta(days=1),
            "end": dates[1] + timedelta(days=1),
        },
        secure=True,
    )
    assert response.status_code == 302
    response = browser.post(
        f"/c/default/reservations/{item.pk}/cancel/",
        {"csrfmiddlewaretoken": token, "confirm": "on"},
        secure=True,
    )
    assert response.status_code == 302
    response = browser.get("/c/default/campsites/", search, secure=True)
    assert site.name.encode() in response.content


def test_map_does_not_expose_private_data(browser, booking, dates):
    response = browser.get("/c/default/map/", {"start": dates[0], "end": dates[1]}, secure=True)
    assert response.status_code == 200
    assert b"map-reserved" in response.content
    assert booking.camper.email.encode() not in response.content
    assert str(booking.pk).encode() not in response.content
    assert Client().get("/c/default/map/", secure=True).status_code == 302


def test_signup_duplicate_generic_response(client, camper, password):
    payload = {
        "first_name": "Test",
        "last_name": "Camper",
        "password1": password,
        "password2": password,
        "rules_agreed": "on",
        "policies_agreed": "on",
        "username": "fresh",
        "email": "fresh@example.test",
    }
    first = client.post("/c/default/accounts/signup/", payload, secure=True)
    different_email = client.post(
        "/c/default/accounts/signup/", {**payload, "email": "second@example.test"}, secure=True
    )
    duplicate_email = client.post(
        "/c/default/accounts/signup/",
        {**payload, "username": "second", "email": "FRESH@example.test"},
        secure=True,
    )
    assert first.status_code == different_email.status_code == duplicate_email.status_code == 302
    assert first.url == different_email.url == duplicate_email.url
    assert "_auth_user_id" not in client.session
    assert User.objects.filter(email__in=["fresh@example.test", "second@example.test"]).count() == 2


def test_role_setup_and_protected_operator_authorization(camper):
    output = StringIO()
    call_command("setup_roles", stdout=output)
    call_command(
        "authorize_account",
        camper.email,
        role="Administrator",
        attest_identity_checked=True,
        stdout=output,
    )
    camper.refresh_from_db()
    assert camper.is_staff and not camper.is_superuser
    assert camper.has_perm("configuration.change_campground")
    assert not camper.has_perm("auth.change_permission")
    assert not camper.has_perm("accounts.change_user")


def test_demo_seed_is_idempotent_and_forbidden_in_production(monkeypatch):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.production")
    with pytest.raises(CommandError):
        call_command("seed_demo_data", stdout=StringIO())
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.testing")
    call_command("seed_demo_data", stdout=StringIO())
    call_command("seed_demo_data", stdout=StringIO())
    assert Campsite.objects.count() == 30
    assert not User.objects.exists()


def test_invitation_secret_file_and_audit(staff, tmp_path):
    import hashlib

    from apps.accounts.models import Invitation
    from apps.audit.models import Event

    tmp_path.chmod(0o700)
    path = tmp_path / "invitation"
    output = StringIO()
    call_command("create_invitation", actor=staff.email, output=path, stdout=output)
    assert path.stat().st_mode & 0o077 == 0
    token = path.read_text()
    secret_not_output = token not in output.getvalue()
    secret_not_stored = token != Invitation.objects.get().digest
    assert secret_not_output and secret_not_stored
    assert Invitation.objects.get().digest == hashlib.sha256(token.encode()).hexdigest()
    assert Event.objects.filter(action="invitation.created").exists()


def test_expiry_command_and_notification_mark_read(browser, booking):
    from apps.notifications.models import Notification

    item = Notification.objects.get(recipient=booking.camper)
    client = Client()
    client.force_login(
        booking.camper, backend="allauth.account.auth_backends.AuthenticationBackend"
    )
    assert client.post(f"/c/default/notifications/{item.pk}/read/", secure=True).status_code == 302
    item.refresh_from_db()
    assert item.read_at is not None
    call_command("expire_reservations", stdout=StringIO())
