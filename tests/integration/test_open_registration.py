"""Open registration permits normal booking without an operator approving an account."""

import uuid

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.reservations.models import Occupancy
from tests.security.test_google_oauth import (
    PREFIX,
    callback,
    google,  # noqa: F401
    post,
    signing_key,  # noqa: F401
    start,
)

pytestmark = pytest.mark.django_db


def reserve(browser, site, dates):
    page = browser.get(f"/c/default/campsites/{site.pk}/reserve/", secure=True)
    assert page.status_code == 200
    response = browser.post(
        f"/c/default/campsites/{site.pk}/reserve/",
        {
            "start": dates[0],
            "end": dates[1],
            "adults": 1,
            "children": 0,
            "pets": 0,
            "rv_length": 0,
            "notes": "Synthetic open-registration test",
            "submission_key": uuid.uuid4(),
        },
        secure=True,
        HTTP_ORIGIN="https://testserver",
        HTTP_X_CSRFTOKEN=browser.cookies["__Host-csrftoken"].value,
    )
    assert response.status_code == 302
    reservation = Occupancy.objects.get(campsite=site)
    assert reservation.status == "confirmed"
    assert str(reservation.camper_id) == browser.session["_auth_user_id"]


def check_camper(email):
    user = User.objects.get(email=email)
    assert user.approved and user.is_active
    assert not user.is_staff and not user.is_superuser and not user.get_all_permissions()
    assert list(user.groups.values_list("name", flat=True)) == ["Camper"]
    return user


def test_local_open_signup_can_login_and_book_without_operator(policy, password, site, dates):
    policy.registration_mode = "open"
    policy.save()
    browser = Client(enforce_csrf_checks=True)
    response = post(
        browser,
        PREFIX + "signup/",
        {
            "email": "new-open@example.test",
            "first_name": "Test",
            "last_name": "Camper",
            "password1": password,
            "password2": password,
            "rules_agreed": True,
            "policies_agreed": True,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    assert response.status_code == 302
    assert "_auth_user_id" not in browser.session  # Preserve uniform anti-enumeration completion.
    check_camper("new-open@example.test")
    login = post(
        browser, PREFIX + "login/", {"login": "new-open@example.test", "password": password}
    )
    assert login.status_code == 302
    reserve(browser, site, dates)


@pytest.mark.usefixtures("google")
def test_google_open_signup_can_login_and_book_without_operator(
    policy,
    site,
    dates,
    monkeypatch,
    signing_key,  # noqa: F811
):
    policy.registration_mode = "open"
    policy.save()
    browser = Client(enforce_csrf_checks=True)
    claims = {"email": "new-open-google@gmail.com"}
    response, _ = callback(browser, start(browser), monkeypatch, signing_key, claims=claims)
    assert response.status_code == 302 and response.url.endswith("/3rdparty/signup/")
    registered = post(
        browser,
        response.url,
        {
            "first_name": "Test",
            "last_name": "Camper",
            "rules_agreed": True,
            "policies_agreed": True,
            "is_staff": True,
            "is_superuser": True,
        },
    )
    assert registered.status_code == 302
    assert "_auth_user_id" not in browser.session
    check_camper(claims["email"])
    login, _ = callback(browser, start(browser), monkeypatch, signing_key, claims=claims)
    assert login.status_code == 302 and login.url == "/c/default/dashboard/"
    reserve(browser, site, dates)
