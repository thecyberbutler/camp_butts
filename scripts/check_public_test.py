"""Verify the public test deployment without printing cookies, headers or response bodies."""

import http.client
import socket
import ssl
import sys

HOST = "camp-butts-test.thecyberbutler.io"
PREFIX = "/c/georgia-mountain-fairgrounds"
BANNER = b"THIS IS A TEST INSTANCE"


class ValidationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def check():
    context = ssl.create_default_context()

    def request(path, *, method="GET", headers=None, body=None):
        connection = http.client.HTTPSConnection(HOST, context=context, timeout=15)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            data = response.read(2 * 1024 * 1024 + 1)
            require(len(data) <= 2 * 1024 * 1024, "Unexpected response size")
            return response.status, {k.lower(): v for k, v in response.getheaders()}, data
        finally:
            connection.close()

    for path, expected in (
        ("/", 200),
        (PREFIX + "/", 200),
        (PREFIX + "/accounts/login/", 200),
        (PREFIX + "/accounts/signup/", 200),
        (PREFIX + "/campsites/", 200),
        (PREFIX + "/missing/", 404),
    ):
        status, headers, data = request(path)
        require(status == expected, "Unexpected page status")
        require(data.count(BANNER) == 1, "Missing or duplicate test banner")
        require(headers.get("x-content-type-options") == "nosniff", "Missing nosniff")
        require("max-age=31536000" in headers.get("strict-transport-security", ""), "Missing HSTS")
        require("default-src 'none'" in headers.get("content-security-policy", ""), "Missing CSP")
        require("no-store" in headers.get("cache-control", ""), "Missing private cache policy")
    for path in (
        "/static/vendor/bootstrap.min.css",
        "/static/vendor/htmx.min.js",
        "/static/css/app.css",
    ):
        status, _, data = request(path)
        require(status == 200, "Missing local static asset")
        if path.endswith("app.css"):
            require(
                b".test-instance-banner" in data and b"#b91c1c" in data, "Missing red banner CSS"
            )
    status, _, _ = request("/", headers={"Host": "untrusted.invalid"})
    require(status in (404, 421), "Unknown host routed to application")
    status, _, _ = request(
        "/",
        headers={"X-Forwarded-Proto": "http", "X-Real-IP": "invalid", "Forwarded": "proto=http"},
    )
    require(status == 200, "Forwarding-header boundary failed")
    status, _, data = request(PREFIX + "/accounts/login/", method="POST", body=b"login=synthetic")
    require(status == 403 and BANNER in data, "CSRF or error banner check failed")
    status, _, _ = request(PREFIX + "/accounts/login/", method="POST", body=b"x" * 65537)
    require(status == 413, "Request body limit not enforced")
    for path in ("/api/rawdata", "/dashboard/", "/static/%2e%2e/.secrets/django_key"):
        status, _, _ = request(path)
        require(status != 200, "Unexpected private resource exposure")
    plain = http.client.HTTPConnection(HOST, timeout=15)
    try:
        plain.request("GET", "/")
        response = plain.getresponse()
        require(response.status in (301, 308), "HTTP did not redirect")
        require(response.getheader("Location") == f"https://{HOST}/", "Unexpected redirect target")
        response.read()
    finally:
        plain.close()
    with socket.create_connection((HOST, 443), timeout=15) as sock:
        try:
            with context.wrap_socket(sock, server_hostname="untrusted.invalid"):
                raise ValidationError("Unknown SNI accepted")
        except ssl.SSLCertVerificationError:
            raise ValidationError("Unknown SNI received a fallback certificate") from None
        except ssl.SSLError:
            pass
    print(
        "Public HTTPS, banner, static assets, security headers, CSRF, "
        "host/SNI and body limits verified."
    )


if __name__ == "__main__":
    try:
        check()
    except Exception as error:
        message = (
            str(error) if isinstance(error, ValidationError) else "Transport/configuration failure"
        )
        print(f"Public test validation failed: {message}", file=sys.stderr)
        raise SystemExit(1) from None
