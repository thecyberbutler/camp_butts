"""Validate a running isolated localhost proxy without logging headers or bodies."""

import argparse
import http.client
import ssl
import sys
from pathlib import Path


class BoundaryError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise BoundaryError(message)


def check(ca_file: Path, https_port: int, http_port: int, campground: str):
    import re

    require(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", campground)), "Invalid campground")
    prefix = f"/c/{campground}"
    context = ssl.create_default_context(cafile=str(ca_file))

    def request(path, *, method="GET", headers=None, body=None):
        connection = http.client.HTTPSConnection(
            "localhost", https_port, context=context, timeout=15
        )
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            result = (response.status, dict(response.getheaders()), response.read())
            return result
        finally:
            connection.close()

    for path in (
        "/",
        prefix + "/",
        "/static/vendor/bootstrap.min.css",
        "/static/vendor/htmx.min.js",
    ):
        status, headers, _ = request(path)
        require(status == 200, "Expected application/static response")
        lower = {key.lower(): value for key, value in headers.items()}
        require(lower.get("x-content-type-options") == "nosniff", "Missing nosniff")
        require("max-age=31536000" in lower.get("strict-transport-security", ""), "Missing HSTS")
        require("default-src 'none'" in lower.get("content-security-policy", ""), "Missing CSP")
        require("access-control-allow-origin" not in lower, "Unexpected static CORS")
    status, _, _ = request(
        "/",
        headers={
            "X-Forwarded-Proto": "http",
            "X-Real-IP": "invalid-attacker-input",
            "X-Forwarded-For": "198.51.100.23",
            "Forwarded": "for=198.51.100.23;proto=http",
        },
    )
    require(status == 200, "Spoofed forwarding headers reached Django")
    status, _, _ = request("/", headers={"Host": "untrusted.invalid"})
    require(status in (404, 421), "Unknown host routed to application")
    status, _, _ = request(prefix + "/accounts/login/", method="POST", body=b"x" * 65537)
    require(status == 413, "Proxy body limit not enforced")
    status, _, _ = request(prefix + "/accounts/login/", method="POST", body=b"login=synthetic")
    require(status == 403, "CSRF protection not enforced through proxy")
    for path in (
        "/static/../.secrets/django_key",
        "/static/%2e%2e/.secrets/django_key",
        "/api/rawdata",
        "/dashboard/#/",
    ):
        status, _, _ = request(path)
        require(status != 200, "Unexpected private file or dashboard exposure")
    plain = http.client.HTTPConnection("localhost", http_port, timeout=15)
    try:
        plain.request("GET", "/", headers={"X-Forwarded-Proto": "https"})
        response = plain.getresponse()
        require(response.status in (301, 308), "HTTP did not redirect")
        require(
            response.getheader("Location") == f"https://localhost:{https_port}/", "Unsafe redirect"
        )
        response.read()
    finally:
        plain.close()
    import socket

    with socket.create_connection(("localhost", https_port), timeout=10) as sock:
        try:
            with context.wrap_socket(sock, server_hostname="untrusted.invalid"):
                raise BoundaryError("Unknown SNI accepted")
        except ssl.SSLCertVerificationError:
            raise BoundaryError("Unknown SNI received a fallback certificate") from None
        except ssl.SSLError:
            pass
    print("HTTPS, static assets, headers, host/SNI, request size and CSRF boundaries verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campground", required=True)
    parser.add_argument("--ca-file", required=True, type=Path)
    parser.add_argument("--https-port", type=int, default=443)
    parser.add_argument("--http-port", type=int, default=80)
    args = parser.parse_args()
    try:
        check(args.ca_file, args.https_port, args.http_port, args.campground)
    except Exception as error:
        message = (
            str(error) if isinstance(error, BoundaryError) else "Transport/configuration failure"
        )
        print(f"Proxy boundary validation failed: {message}", file=sys.stderr)
        raise SystemExit(1) from None
