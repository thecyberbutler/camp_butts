import secrets
import time

import pytest
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator
from allauth.mfa.recovery_codes.internal.auth import RecoveryCodes
from allauth.mfa.totp.internal.auth import TOTP, format_hotp_value, generate_totp_secret, hotp_value
from django.db import IntegrityError, transaction
from django.test import Client

from apps.accounts.adapters import MFAAdapter
from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def registration(password, **overrides):
    return {
        "username": "newcamper",
        "email": "new@example.test",
        "first_name": "New",
        "last_name": "Camper",
        "phone": "",
        "password1": password,
        "password2": password,
        "rules_agreed": "on",
        "policies_agreed": "on",
        **overrides,
    }


def test_signup_cannot_escalate(client, password):
    response = client.post(
        "/accounts/signup/",
        registration(password, is_staff="true", is_superuser="true", approved="true"),
        secure=True,
    )
    assert response.status_code == 302
    user = User.objects.get(username="newcamper")
    assert not user.is_staff and not user.is_superuser and not user.approved
    assert user.groups.filter(name="Camper").exists()
    assert user.password.startswith("argon2$")
    assert user.policy_accepted_at and user.policy_version


def test_registration_modes(client, password, policy):
    policy.registration_mode = "disabled"
    policy.save()
    response = client.post("/accounts/signup/", registration(password), secure=True)
    assert response.status_code == 200
    assert not User.objects.filter(username="newcamper").exists()
    policy.registration_mode = "open"
    policy.save()
    assert client.post("/accounts/signup/", registration(password), secure=True).status_code == 302
    assert User.objects.get(username="newcamper").approved


def test_case_insensitive_uniqueness(camper):
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(username=camper.username.upper(), email="different@example.test")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(username="different", email=camper.email.upper())


def test_login_logout_and_secure_session(client, camper, password):
    assert (
        client.post(
            "/accounts/login/", {"login": camper.username, "password": password}, secure=True
        ).status_code
        == 302
    )
    assert client.get("/dashboard/", secure=True).status_code == 200
    from django.conf import settings

    assert client.cookies[settings.SESSION_COOKIE_NAME]["secure"]
    assert client.cookies[settings.SESSION_COOKIE_NAME]["httponly"]
    assert client.post("/accounts/logout/", secure=True).status_code == 302
    assert client.get("/dashboard/", secure=True).status_code == 302


def test_login_rate_limiting_and_case_normalization(client, camper, password):
    for _ in range(5):
        client.post(
            "/accounts/login/",
            {"login": camper.username.upper(), "password": secrets.token_urlsafe(24)},
            secure=True,
        )
    response = client.post(
        "/accounts/login/", {"login": camper.username, "password": password}, secure=True
    )
    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert "_auth_user_id" not in client.session


def test_encrypted_totp_and_single_use_recovery(camper):
    secret = generate_totp_secret()
    authenticator = TOTP.activate(camper, secret)
    assert secret not in str(authenticator.instance.data)
    assert MFAAdapter().decrypt(authenticator.instance.data["secret"]) == secret
    codes = RecoveryCodes.activate(camper)
    code = codes.get_unused_codes()[0]
    assert code not in str(codes.instance.data)
    assert codes.validate_code(code)
    assert not codes.validate_code(code)


def test_actual_staff_login_requires_totp(staff, password):
    secret = generate_totp_secret()
    TOTP.activate(staff, secret)
    EmailAddress.objects.create(user=staff, email=staff.email, verified=True, primary=True)
    client = Client()
    response = client.post(
        "/accounts/login/", {"login": staff.username, "password": password}, secure=True
    )
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session
    assert (
        client.post("/accounts/2fa/authenticate/", {"code": "invalid"}, secure=True).status_code
        == 200
    )
    assert "_auth_user_id" not in client.session
    code = format_hotp_value(hotp_value(secret, int(time.time()) // 30))
    response = client.post("/accounts/2fa/authenticate/", {"code": code}, secure=True)
    assert response.status_code == 302
    assert client.get("/dashboard/", secure=True).status_code == 200
    assert not MFAAdapter().can_delete_authenticator(
        Authenticator.objects.get(user=staff, type="totp")
    )
