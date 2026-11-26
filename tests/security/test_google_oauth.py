"""Exercise actual allauth callbacks with locally signed synthetic Google assertions."""

import hashlib
import html
import json
import re
import secrets
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
import requests
from allauth.account.models import EmailAddress
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from django.core.exceptions import ImproperlyConfigured
from django.test import Client

from apps.accounts.models import Invitation, User
from apps.google_auth.adapter import GoogleAccountAdapter
from apps.google_auth.transport import GoogleSession
from apps.tenancy.context import tenant_scope
from config.google import google_configuration
from tests.security.test_tenancy import second_tenant  # noqa: F401

PREFIX = "/c/default/accounts/"
CLIENT_ID = "1234567890-synthetic.apps.googleusercontent.com"


@pytest.fixture
def google(settings):
    settings.GOOGLE_OAUTH_APPS = {
        "default": {"client_id": CLIENT_ID, "secret": secrets.token_urlsafe(32)}
    }
    return settings.GOOGLE_OAUTH_APPS["default"]


@pytest.fixture(scope="module")
def signing_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Synthetic OAuth test")])
    now = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=1))
        .sign(key, hashes.SHA256())
    )
    return key, cert.public_bytes(serialization.Encoding.PEM).decode()


def post(client, path, data=None):
    client.get(PREFIX + "login/", secure=True)
    if "__Host-csrftoken" not in client.cookies:
        client.get(PREFIX + "logout/", secure=True)
    return client.post(
        path,
        data or {},
        secure=True,
        HTTP_X_CSRFTOKEN=client.cookies["__Host-csrftoken"].value,
        HTTP_ORIGIN="https://testserver",
    )


def start(client, process="login", suffix=""):
    response = post(client, PREFIX + "google/login/" + suffix, {"process": process})
    assert response.status_code == 200
    match = re.search(rb'id="google-signin-redirect" href="([^"]+)"', response.content)
    assert match
    url = html.unescape(match[1].decode())
    assert urlsplit(url).netloc == "accounts.google.com"
    return {key: values[0] for key, values in parse_qs(urlsplit(url).query).items()}


def callback(
    client, authorization, monkeypatch, signing_key, *, claims=None, algorithm="RS256", perform=True
):
    key, cert = signing_key
    data = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
        "sub": "12345678901234567890",
        "nonce": authorization["nonce"],
        "email": "camper@example.test",
        "email_verified": True,
    }
    data.update(claims or {})
    data = {k: v for k, v in data.items() if v is not None}
    credential = jwt.encode(
        data,
        key if algorithm == "RS256" else secrets.token_bytes(32),
        algorithm=algorithm,
        headers={"kid": "synthetic"},
    )
    token = secrets.token_urlsafe(32)
    calls = []

    def request(self, method, url, **kwargs):
        calls.append((method, url))
        response = requests.Response()
        response.status_code = 200
        response.headers["content-type"] = "application/json"
        if url.endswith("/token"):
            assert kwargs["data"]["code_verifier"]
            assert kwargs["data"]["redirect_uri"] == (
                "https://testserver/c/default/accounts/google/login/callback/"
            )
            payload = {"access_token": token, "id_token": credential, "token_type": "Bearer"}
        else:
            assert url == "https://www.googleapis.com/oauth2/v1/certs"
            payload = {"synthetic": cert}
        response._content = json.dumps(payload).encode()
        return response

    monkeypatch.setattr(GoogleSession, "request", request)
    if not perform:
        return calls
    response = client.get(
        PREFIX + "google/login/callback/",
        {"state": authorization["state"], "code": secrets.token_urlsafe(24)},
        secure=True,
    )
    assert token.encode() not in response.content and credential.encode() not in response.content
    assert not SocialToken.objects.exists()
    return response, calls


def test_disabled_provider_is_not_advertised_or_reachable(client):
    assert b"Continue with Google" not in client.get(PREFIX + "login/", secure=True).content
    for path in ("google/login/", "google/login/callback/", "google/login/token/", "3rdparty/"):
        assert client.get(PREFIX + path, secure=True).status_code == 404


def test_start_requires_csrf_and_fixes_scope_redirect_pkce_and_nonce(google):
    client = Client(enforce_csrf_checks=True)
    assert client.post(PREFIX + "google/login/", {}, secure=True).status_code == 403
    assert client.get(PREFIX + "google/login/", secure=True).status_code == 200
    params = start(
        client,
        suffix="?scope=https://evil.invalid&auth_params=access_type%3Doffline&next=https://evil.invalid",
    )
    assert set(params["scope"].split()) == {"openid", "email"}
    assert params["access_type"] == "online" and params["code_challenge_method"] == "S256"
    assert len(params["nonce"]) >= 32 and len(params["state"]) >= 32
    assert params["redirect_uri"].endswith("/c/default/accounts/google/login/callback/")
    assert google["secret"] not in json.dumps(params)
    assert client.get(PREFIX + "google/login/token/", secure=True).status_code == 404


def test_existing_google_login_rotates_session_and_rejects_state_replay(
    google, camper, monkeypatch, signing_key
):
    SocialAccount.objects.create(user=camper, provider="google", uid="12345678901234567890")
    client = Client(enforce_csrf_checks=True)
    auth = start(client)
    previous = client.session.session_key
    response, calls = callback(client, auth, monkeypatch, signing_key)
    assert response.status_code == 302 and response.url == "/c/default/dashboard/"
    assert client.session.session_key != previous
    assert client.session["_auth_user_id"] == str(camper.pk)
    assert len(calls) == 2
    before = len(calls)
    replay = client.get(
        PREFIX + "google/login/callback/", {"state": auth["state"], "code": "replay"}, secure=True
    )
    assert replay.status_code == 403 and len(calls) == before
    assert SocialAccount.objects.get().extra_data == {"email": camper.email}


@pytest.mark.parametrize(
    "claims",
    [
        {"iss": "https://attacker.invalid"},
        {"aud": "different-client"},
        {"azp": "different-client"},
        {"exp": 1},
        {"exp": None},
        {"iat": int(time.time()) + 3600},
        {"nonce": "different-nonce"},
        {"nonce": None},
        {"email_verified": False},
        {"email_verified": "true"},
        {"email": "not-an-email"},
        {"sub": ""},
    ],
)
def test_invalid_oidc_claims_never_authenticate(google, camper, monkeypatch, signing_key, claims):
    SocialAccount.objects.create(user=camper, provider="google", uid="12345678901234567890")
    client = Client()
    response, _ = callback(client, start(client), monkeypatch, signing_key, claims=claims)
    assert response.status_code == 403 and "_auth_user_id" not in client.session


def test_rejects_unapproved_algorithm(google, camper, monkeypatch, signing_key):
    client = Client()
    response, calls = callback(client, start(client), monkeypatch, signing_key, algorithm="HS256")
    assert response.status_code == 403 and len(calls) == 1


@pytest.mark.parametrize("attribute", ["approved", "is_active"])
def test_ineligible_accounts_cannot_use_google(google, camper, monkeypatch, signing_key, attribute):
    setattr(camper, attribute, False)
    camper.save()
    SocialAccount.objects.create(user=camper, provider="google", uid="12345678901234567890")
    client = Client()
    response, _ = callback(client, start(client), monkeypatch, signing_key)
    assert response.status_code == 403 and "_auth_user_id" not in client.session


def test_google_login_still_requires_enrolled_mfa(google, staff, monkeypatch, signing_key):
    TOTP.activate(staff, generate_totp_secret())
    EmailAddress.objects.create(user=staff, email=staff.email, verified=True, primary=True)
    SocialAccount.objects.create(user=staff, provider="google", uid="12345678901234567890")
    client = Client()
    response, _ = callback(
        client, start(client), monkeypatch, signing_key, claims={"email": staff.email}
    )
    assert response.status_code == 302 and response.url.endswith("/2fa/authenticate/")
    assert "_auth_user_id" not in client.session


def test_same_email_does_not_link_or_log_in_existing_user(google, camper, monkeypatch, signing_key):
    client = Client()
    response, _ = callback(client, start(client), monkeypatch, signing_key)
    assert response.status_code == 302 and response.url.endswith("/3rdparty/signup/")
    assert "_auth_user_id" not in client.session and not SocialAccount.objects.exists()
    result = post(
        client,
        response.url,
        {
            "email": "tampered@example.test",
            "first_name": "Test",
            "last_name": "Camper",
            "rules_agreed": True,
            "policies_agreed": True,
        },
    )
    assert result.status_code == 302 and result.url.endswith("/registration-received/")
    assert User.objects.count() == 1 and not SocialAccount.objects.exists()


@pytest.mark.parametrize("mode", ["approval", "open", "invitation", "disabled"])
def test_google_registration_preserves_policy_and_never_auto_logs_in(
    google, policy, camper, monkeypatch, signing_key, mode
):
    policy.registration_mode = mode
    policy.save()
    invite = secrets.token_urlsafe(32)
    Invitation.objects.create(
        digest=hashlib.sha256(invite.encode()).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_by=camper,
    )
    client = Client()
    response, _ = callback(
        client, start(client), monkeypatch, signing_key, claims={"email": "newcamper@gmail.com"}
    )
    if mode == "disabled":
        assert not SocialAccount.objects.exists()
        assert "_auth_user_id" not in client.session
        return
    assert response.status_code == 302
    pending = client.session.get("socialaccount_sociallogin", {})
    assert not pending.get("token")
    assert pending["account"]["extra_data"] == {"email": "newcamper@gmail.com"}
    payload = {
        "email": "tampered@example.test",
        "first_name": "Test",
        "last_name": "Camper",
        "rules_agreed": True,
        "policies_agreed": True,
        "invitation": invite,
        "approved": True,
        "is_staff": True,
    }
    missing = post(client, response.url, {**payload, "rules_agreed": False})
    assert (
        missing.status_code == 200 and not User.objects.filter(email="newcamper@gmail.com").exists()
    )
    result = post(client, response.url, payload)
    assert result.status_code == 302 and result.url.endswith("/registration-received/")
    user = User.objects.get(email="newcamper@gmail.com")
    assert user.approved == (mode in {"open", "invitation"})
    assert not user.is_staff and not user.is_superuser and not user.has_usable_password()
    assert user.groups.filter(name="Camper").exists() and user.policy_accepted_at
    assert user.email == "newcamper@gmail.com"
    assert EmailAddress.objects.get(user=user).verified
    assert "_auth_user_id" not in client.session and not SocialToken.objects.exists()
    assert "token" not in client.session.get("socialaccount_sociallogin", {})


def test_connect_requires_password_assurance_and_revokes_sessions(
    google, camper, password, monkeypatch, signing_key
):
    client = Client()
    client.force_login(camper, backend="allauth.account.auth_backends.AuthenticationBackend")
    assert post(client, PREFIX + "google/login/", {"process": "connect"}).status_code == 403
    post(client, PREFIX + "reauthenticate/", {"password": password})
    auth = start(client, "connect")
    response, _ = callback(client, auth, monkeypatch, signing_key)
    assert response.status_code == 302 and SocialAccount.objects.get().user_id == camper.pk
    camper.refresh_from_db()
    assert camper.security_version == 2
    assert client.get("/c/default/dashboard/", secure=True).status_code == 302


def test_disconnect_requires_password_assurance_and_revokes_sessions(google, camper, password):
    account = SocialAccount.objects.create(user=camper, provider="google", uid="synthetic")
    client = Client(enforce_csrf_checks=True)
    post(client, PREFIX + "login/", {"login": camper.email, "password": password})
    post(client, PREFIX + "reauthenticate/", {"password": password})
    assert post(client, PREFIX + "3rdparty/", {"account": account.pk}).status_code == 302
    assert not SocialAccount.objects.exists()
    camper.refresh_from_db()
    assert camper.security_version == 2
    assert client.get("/c/default/dashboard/", secure=True).status_code == 302
    account = SocialAccount.objects.create(user=camper, provider="google", uid="synthetic")
    client.force_login(camper, backend="allauth.account.auth_backends.AuthenticationBackend")
    assert post(client, PREFIX + "3rdparty/", {"account": account.pk}).status_code == 403
    assert SocialAccount.objects.filter(pk=account.pk).exists()


def test_state_and_accounts_do_not_cross_tenants(
    google,
    camper,
    second_tenant,  # noqa: F811
    settings,
    monkeypatch,
):
    settings.GOOGLE_OAUTH_APPS = {**settings.GOOGLE_OAUTH_APPS, "second": google}
    SocialAccount.objects.create(user=camper, provider="google", uid="12345678901234567890")
    client = Client()
    auth = start(client)

    def forbidden_request(*args, **kwargs):
        pytest.fail("Cross-tenant callback reached Google transport")

    monkeypatch.setattr(GoogleSession, "request", forbidden_request)
    response = client.get(
        "/c/second/accounts/google/login/callback/",
        {"state": auth["state"], "code": "synthetic"},
        secure=True,
    )
    assert response.status_code == 403
    with tenant_scope(second_tenant):
        assert not SocialAccount.objects.exists()


def test_google_configuration_is_file_only_and_rejects_invalid_or_public_file(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("GOOGLE_OAUTH_CONFIG_FILE", raising=False)
    assert google_configuration() == {}
    path = tmp_path / "google.json"
    path.touch(mode=0o600)
    valid = {"default": {"client_id": CLIENT_ID, "secret": secrets.token_urlsafe(32)}}
    path.write_text(json.dumps(valid))
    monkeypatch.setenv("GOOGLE_OAUTH_CONFIG_FILE", str(path))
    assert google_configuration() == valid
    path.chmod(0o644)
    with pytest.raises(ImproperlyConfigured):
        google_configuration()
    path.chmod(0o600)
    path.write_text(
        json.dumps({"default": {**valid["default"], "endpoint": "https://evil.invalid"}})
    )
    with pytest.raises(ImproperlyConfigured):
        google_configuration()


def test_database_social_apps_cannot_override_file_configuration(google, rf):
    from apps.tenancy.context import current_tenant

    SocialApp.objects.create(provider="google", client_id="untrusted", secret="synthetic")
    request = rf.get("/")
    request.tenant = current_tenant()
    apps = GoogleAccountAdapter().list_apps(request)
    assert len(apps) == 1 and apps[0].client_id == CLIENT_ID and apps[0].pk is None


@pytest.mark.parametrize(
    "url",
    [
        "http://oauth2.googleapis.com/token",
        "https://169.254.169.254/",
        "https://oauth2.googleapis.com/token?extra=1",
        "https://evil.invalid/",
    ],
)
def test_transport_denies_nonallowlisted_urls(url):
    with GoogleSession() as session, pytest.raises(requests.RequestException):
        session.post(url)


def test_transport_forces_tls_proxy_bounds_and_no_redirect(monkeypatch):
    calls = []

    def request(self, method, url, **kwargs):
        calls.append(kwargs)
        response = requests.Response()
        response.status_code = 302
        response._content = b""
        response._content_consumed = True
        return response

    monkeypatch.setattr(requests.Session, "request", request)
    with GoogleSession() as session, pytest.raises(requests.RequestException):
        session.post("https://oauth2.googleapis.com/token", verify=False, allow_redirects=True)
    assert calls[0]["verify"] is True and calls[0]["allow_redirects"] is False
    assert calls[0]["proxies"] == {"https": "http://google-egress:3128"}


def test_expired_state_and_rate_limits_fail_before_network(google, monkeypatch):
    client = Client()
    auth = start(client)
    session = client.session
    state, timestamp, provider = session["socialaccount_states"][auth["state"]]
    state["created_at"] = time.time() - 301
    session["socialaccount_states"][auth["state"]] = [state, timestamp, provider]
    session.save()

    def forbidden_request(*args, **kwargs):
        pytest.fail("Invalid/expired state must not reach the provider")

    monkeypatch.setattr(GoogleSession, "request", forbidden_request)
    response = client.get(
        PREFIX + "google/login/callback/",
        {"state": auth["state"], "code": "synthetic"},
        secure=True,
    )
    assert response.status_code == 403
    for _ in range(10):
        response = client.post(PREFIX + "google/login/", {}, secure=True)
    assert response.status_code == 429


def test_axes_lockout_cannot_be_bypassed_with_google(google, camper, monkeypatch, signing_key):
    client = Client()
    for _ in range(5):
        client.post(
            PREFIX + "login/",
            {"login": camper.email, "password": secrets.token_urlsafe(32)},
            secure=True,
        )
    SocialAccount.objects.create(user=camper, provider="google", uid="12345678901234567890")
    response, _ = callback(client, start(client), monkeypatch, signing_key)
    assert response.status_code == 403 and "_auth_user_id" not in client.session


@pytest.mark.django_db(transaction=True)
@pytest.mark.concurrency
def test_simultaneous_callbacks_consume_state_once(google, camper, monkeypatch, signing_key):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    SocialAccount.objects.create(user=camper, provider="google", uid="12345678901234567890")
    client = Client()
    auth = start(client)
    calls = callback(client, auth, monkeypatch, signing_key, perform=False)
    cookie = client.cookies["__Host-sessionid"].value
    barrier = Barrier(2)

    def attempt():
        close_old_connections()
        try:
            browser = Client()
            browser.cookies["__Host-sessionid"] = cookie
            barrier.wait(timeout=10)
            return browser.get(
                PREFIX + "google/login/callback/",
                {"state": auth["state"], "code": "synthetic"},
                secure=True,
            ).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt(), range(2)))
    assert sorted(results) == [302, 403]
    assert sum(method == "POST" for method, _ in calls) == 1
