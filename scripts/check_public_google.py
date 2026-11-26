"""Probe the public Google entry flow; never display cookies, state or response bodies."""

import html
import re
from urllib.parse import parse_qs, urlsplit

import requests

GOOGLE_SCOPES = {
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/user.phonenumbers.read",
}

ORIGIN = "https://camp-butts-test.thecyberbutler.io"
PREFIX = ORIGIN + "/c/georgia-mountain-fairgrounds/accounts/"
CLIENT_ID = "232928548083-ipnfvophvjhhb8bq0rdcu3iqmpfu8ets.apps.googleusercontent.com"


def require(condition):
    if not condition:
        raise ValueError("Public Google boundary check failed")


def check():
    with requests.Session() as browser:
        browser.trust_env = False
        # The local host CA file is needed on macOS; TLS verification remains mandatory.
        browser.verify = "/etc/ssl/cert.pem"

        def request(method, path, **kwargs):
            response = browser.request(
                method, PREFIX + path, timeout=(5, 15), allow_redirects=False, **kwargs
            )
            require("default-src 'none'" in response.headers.get("Content-Security-Policy", ""))
            require("form-action 'self'" in response.headers["Content-Security-Policy"])
            require(b"THIS IS A TEST INSTANCE" in response.content)
            return response

        response = request("GET", "login/")
        require(response.status_code == 200 and "Continue with Google" in response.text)
        response = request("POST", "google/login/", data={"process": "login"})
        require(response.status_code == 403)
        token = browser.cookies.get("__Host-csrftoken")
        require(token)
        response = request(
            "POST",
            "google/login/",
            data={"process": "login"},
            headers={"X-CSRFToken": token, "Origin": ORIGIN},
        )
        require(response.status_code == 200)
        match = re.search(r'id="google-signin-redirect" href="([^"]+)"', response.text)
        require(match)
        url = urlsplit(html.unescape(match[1]))
        require(url.scheme == "https" and url.netloc == "accounts.google.com")
        require(url.path == "/o/oauth2/v2/auth")
        parameters = parse_qs(url.query)
        require(parameters["client_id"] == [CLIENT_ID])
        require(parameters["redirect_uri"] == [PREFIX + "google/login/callback/"])
        require(set(parameters["scope"][0].split()) == set(GOOGLE_SCOPES))
        require(parameters["code_challenge_method"] == ["S256"])
        require(parameters["access_type"] == ["online"])
        require(len(parameters["state"][0]) >= 32 and len(parameters["nonce"][0]) >= 32)
        require(
            request("GET", "google/login/callback/?state=invalid&code=invalid").status_code == 403
        )
        require(request("GET", "google/login/token/").status_code == 404)
    print(
        "Public Google start, CSRF, tenant callback, PKCE, nonce and disabled token route verified."
    )
    print("Real Google consent, token exchange and user sign-in still require an interactive test.")


if __name__ == "__main__":
    try:
        check()
    except Exception:
        raise SystemExit(
            "Public Google validation failed; sensitive diagnostics withheld."
        ) from None
