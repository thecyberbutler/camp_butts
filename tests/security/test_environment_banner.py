"""Deployment labeling must cover full pages without weakening security controls."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.test import Client, RequestFactory

from config.environment import validate_environment
from config.errors import error_content
from config.middleware import ProxyBoundaryMiddleware, ResponseSecurityMiddleware

BANNER = b"THIS IS A TEST INSTANCE"


@pytest.mark.parametrize("environment", ["development", "test", "production"])
@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/c/default/",
        "/c/default/accounts/login/",
        "/c/default/accounts/signup/",
        "/c/default/campsites/",
    ],
)
def test_full_pages_show_banner_only_for_nonproduction(settings, environment, path):
    settings.APP_ENVIRONMENT = environment
    response = Client().get(path, secure=True)
    assert response.status_code == 200
    assert response.content.count(BANNER) == (0 if environment == "production" else 1)
    assert "unsafe-inline" not in response["Content-Security-Policy"]
    assert settings.DEBUG is False
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE


def test_authenticated_pages_and_htmx_do_not_duplicate_banner(settings, browser):
    settings.APP_ENVIRONMENT = "development"
    for path in [
        "/c/default/dashboard/",
        "/c/default/notifications/",
        "/c/default/accounts/logout/",
        "/c/default/accounts/2fa/",
    ]:
        response = browser.get(path, secure=True)
        assert response.status_code == 200
        assert response.content.count(BANNER) == 1
    response = browser.get("/c/default/campsites/", secure=True, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert BANNER not in response.content
    assert b"<html" not in response.content


@pytest.mark.parametrize("environment", ["development", "test", "production"])
@pytest.mark.parametrize("status", [400, 403, 404, 429, 500])
def test_error_pages_need_no_database_and_keep_status_headers(
    settings, environment, status, django_db_blocker
):
    settings.APP_ENVIRONMENT = environment
    response = HttpResponse("Internal diagnostic not for display", status=status)
    response["Retry-After"] = "60"
    response["Content-Length"] = str(len(response.content))
    with django_db_blocker.block():
        result = ResponseSecurityMiddleware(lambda request: response)(RequestFactory().get("/"))
        assert (
            BANNER.decode() in error_content(status)
            if environment != "production"
            else BANNER.decode() not in error_content(status)
        )
    assert result.status_code == status and result["Retry-After"] == "60"
    assert int(result["Content-Length"]) == len(result.content)
    assert result.content.count(BANNER) == (0 if environment == "production" else 1)
    assert b"Internal diagnostic" not in result.content


def test_real_error_paths_and_csrf_include_banner_without_sensitive_details(settings):
    settings.APP_ENVIRONMENT = "test"
    client = Client(enforce_csrf_checks=True)
    responses = [
        client.get("/c/unknown/", secure=True),
        client.get("/c/default/missing/", secure=True),
        client.get("/?campground=invalid/selector", secure=True),
        client.post("/c/default/accounts/login/", {}, secure=True),
        client.get("/", secure=True, HTTP_HOST="unapproved.example"),
    ]
    assert [r.status_code for r in responses] == [404, 404, 400, 403, 400]
    assert all(r.content.count(BANNER) == 1 for r in responses)
    assert all(b"unapproved.example" not in r.content for r in responses)


def test_request_input_cannot_turn_off_banner(settings):
    settings.APP_ENVIRONMENT = "test"
    response = Client().get(
        "/c/default/?APP_ENVIRONMENT=production&show_test_banner=false",
        secure=True,
        HTTP_X_APP_ENVIRONMENT="production",
    )
    assert response.content.count(BANNER) == 1


@pytest.mark.parametrize("value", ["", "prod", "TEST", "test\n", "<script>"])
def test_unknown_environment_fails_closed(value):
    with pytest.raises(ImproperlyConfigured):
        validate_environment(value)


def test_non_html_and_streaming_errors_are_not_rewritten(settings):
    settings.APP_ENVIRONMENT = "test"
    request = RequestFactory().get("/")
    response = JsonResponse({"error": "denied"}, status=403)
    assert ResponseSecurityMiddleware(lambda request: response)(request).content == response.content
    stream = StreamingHttpResponse(iter([b"unavailable"]), status=503)
    assert ResponseSecurityMiddleware(lambda request: stream)(request) is stream


def test_malformed_trusted_proxy_request_has_generic_banner_without_database(
    settings, django_db_blocker
):
    settings.APP_ENVIRONMENT = "development"
    settings.TRUSTED_PROXY_IPS = ["192.0.2.1"]
    request = RequestFactory().get("/", REMOTE_ADDR="192.0.2.1", HTTP_X_REAL_IP="invalid")
    with django_db_blocker.block():
        response = ProxyBoundaryMiddleware(lambda request: None)(request)
    assert response.status_code == 400
    assert response.content.count(BANNER) == 1
    assert b"Invalid proxy" not in response.content
