import logging
import secrets

import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured

from config.logging import SafeFormatter
from config.secrets import read_secret
from config.sessions import SessionStore


def test_missing_secret(monkeypatch):
    monkeypatch.delenv("TEST_SECRET_FILE", raising=False)
    with pytest.raises(ImproperlyConfigured, match="missing"):
        read_secret("TEST_SECRET_FILE")


@pytest.mark.parametrize(
    "mode,content",
    [(0o644, None), (0o600, "placeholder" * 10), (0o600, "x" * 100), (0o600, "too short")],
)
def test_insecure_secret_file_rejected(tmp_path, monkeypatch, mode, content):
    path = tmp_path / "secret"
    path.write_text(content or secrets.token_urlsafe(64))
    path.chmod(mode)
    monkeypatch.setenv("TEST_SECRET_FILE", str(path))
    with pytest.raises(ImproperlyConfigured):
        read_secret("TEST_SECRET_FILE")


def test_symlink_rejected(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.write_text(secrets.token_urlsafe(64))
    target.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(target)
    monkeypatch.setenv("TEST_SECRET_FILE", str(link))
    with pytest.raises(ImproperlyConfigured):
        read_secret("TEST_SECRET_FILE")


def test_session_payload_is_encrypted_and_tampering_fails_closed(settings):
    store = SessionStore()
    marker = secrets.token_urlsafe(24)
    encoded = store.encode({"enrollment": marker})
    plaintext_absent = marker not in encoded
    roundtrip = store.decode(encoded) == {"enrollment": marker}
    assert plaintext_absent and roundtrip
    assert store.decode(encoded[:-5] + "broken") == {}
    settings.SESSION_ENCRYPTION_KEY = Fernet.generate_key().decode()
    assert store.decode(encoded) == {}


def test_logs_never_serialize_message_or_exception():
    marker = secrets.token_urlsafe(24)
    record = logging.LogRecord(
        "django.request",
        logging.ERROR,
        "test",
        1,
        marker,
        (),
        (ValueError, ValueError(marker), None),
    )
    output = SafeFormatter().format(record)
    redacted = marker not in output
    assert redacted
    assert '"component": "django"' in output


def test_settings_keep_required_controls(settings):
    assert not settings.DEBUG
    assert (
        settings.SECURE_SSL_REDIRECT
        and settings.SESSION_COOKIE_SECURE
        and settings.CSRF_COOKIE_SECURE
    )
    assert settings.MFA_ALLOW_UNVERIFIED_EMAIL is False
    assert settings.ACCOUNT_REAUTHENTICATION_REQUIRED
    assert settings.PASSWORD_HASHERS == ["django.contrib.auth.hashers.Argon2PasswordHasher"]
    assert "django.middleware.csrf.CsrfViewMiddleware" in settings.MIDDLEWARE
    assert "axes.middleware.AxesMiddleware" in settings.MIDDLEWARE
