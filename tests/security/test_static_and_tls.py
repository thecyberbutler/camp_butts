import os
from datetime import UTC, datetime

import pytest
from cryptography import x509
from django.test import Client

from scripts.generate_dev_tls import generate

pytestmark = pytest.mark.django_db


def test_static_files_keep_security_headers_and_cannot_escape_root(settings, tmp_path):
    root = tmp_path / "assets"
    root.mkdir()
    (root / "safe.css").write_text("body { color: black; }")
    (tmp_path / "private.txt").write_text("synthetic private fixture")
    settings.STATIC_ROOT = root
    client = Client()
    response = client.get("/static/safe.css", secure=True)
    assert response.status_code == 200
    assert response["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'none'" in response["Content-Security-Policy"]
    assert "max-age=31536000" in response["Strict-Transport-Security"]
    assert "Access-Control-Allow-Origin" not in response
    assert "no-store" in response["Cache-Control"]
    response.close()
    for path in ("/static/../private.txt", "/static/%2e%2e/private.txt", "/static/.secrets/key"):
        assert client.get(path, secure=True).status_code == 404
    # Production must not discover arbitrary newly written files after startup.
    (root / "late.txt").write_text("not in startup asset inventory")
    assert client.get("/static/late.txt", secure=True).status_code == 404
    assert client.post("/static/safe.css", {}, secure=True).status_code == 405
    assert client.get("/static/safe.css").status_code == 301


def test_development_tls_is_localhost_only_and_files_are_protected(tmp_path):
    os.chmod(tmp_path, 0o700)
    target = tmp_path / "tls"
    generate(target)
    cert = x509.load_pem_x509_certificate((target / "localhost.crt").read_bytes())
    ca = x509.load_pem_x509_certificate((target / "ca.crt").read_bytes())
    cert.verify_directly_issued_by(ca)
    issuer_key_id = ca.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest
    authority_key_id = cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value
    assert authority_key_id.key_identifier == issuer_key_id
    assert cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value == (
        x509.SubjectAlternativeName([x509.DNSName("localhost")])
    )
    assert not cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    assert 29 <= (cert.not_valid_after_utc - datetime.now(UTC)).days <= 30
    assert target.stat().st_mode & 0o777 == 0o700
    for path in target.iterdir():
        assert path.stat().st_mode & 0o777 == 0o600
    assert not (target / "ca.key").exists()
    with pytest.raises(FileExistsError):
        generate(target)


def test_development_tls_rejects_unprotected_parent(tmp_path):
    os.chmod(tmp_path, 0o755)
    with pytest.raises(ValueError):
        generate(tmp_path / "tls")
