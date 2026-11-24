import secrets
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from apps.accounts.models import User
from apps.campsites.models import Campsite, CampsiteType
from apps.configuration.models import Campground
from apps.reservations.services import book


@pytest.fixture(autouse=True)
def initial_state(db):
    Campground.objects.get_or_create(pk=1)
    Group.objects.get_or_create(name="Camper")
    cache.clear()


@pytest.fixture
def password():
    return secrets.token_urlsafe(32)


@pytest.fixture
def camper(db, password):
    return User.objects.create_user(
        username="camper", email="camper@example.test", password=password, approved=True
    )


@pytest.fixture
def other(db, password):
    return User.objects.create_user(
        username="other", email="other@example.test", password=password, approved=True
    )


@pytest.fixture
def staff(db, password):
    user = User.objects.create_user(
        username="staff",
        email="staff@example.test",
        password=password,
        approved=True,
        is_staff=True,
    )
    user.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["operate_reservations", "block_campsite", "approve_camper"]
        )
    )
    return user


@pytest.fixture
def policy(db):
    return Campground.current()


@pytest.fixture
def site(db):
    kind = CampsiteType.objects.create(name="Tent")
    return Campsite.objects.create(
        name="Pine 1", site_type=kind, max_occupancy=6, pets_allowed=True, max_rv_length=40
    )


@pytest.fixture
def dates():
    start = timezone.localdate() + timedelta(days=10)
    return start, start + timedelta(days=3)


@pytest.fixture
def booking(camper, site, dates):
    return book(
        actor=camper, campsite_id=site.pk, start=dates[0], end=dates[1], submission_key=uuid.uuid4()
    )


@pytest.fixture
def browser(camper):
    client = Client(enforce_csrf_checks=True)
    client.force_login(camper, backend="allauth.account.auth_backends.AuthenticationBackend")
    return client
