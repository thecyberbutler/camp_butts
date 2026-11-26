import secrets
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import User
from apps.campsites.models import Campsite, CampsiteType
from apps.configuration.models import Campground
from apps.reservations.services import book


@pytest.fixture(scope="session", autouse=True)
def collected_static_assets(tmp_path_factory):
    with override_settings(STATIC_ROOT=tmp_path_factory.mktemp("collected-assets")):
        call_command("collectstatic", interactive=False, verbosity=0)
        yield


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
    return User.objects.create_user(email="camper@example.test", password=password, approved=True)


@pytest.fixture
def other(db, password):
    return User.objects.create_user(email="other@example.test", password=password, approved=True)


@pytest.fixture
def staff(db, password):
    user = User.objects.create_user(
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


@pytest.fixture
def _django_db_helper(request, django_db_setup, django_db_blocker):
    # Wrap pytest-django's own transaction lifecycle, so RLS remains active during
    # its flush/post_migrate teardown as well as the test. No RLS bypass is used.
    from django.db import connection
    from pytest_django.fixtures import _django_db_helper as original

    from apps.tenancy.context import Tenant, _current
    from scripts.tenant_database import prepare_registry, protect_schema

    tenant = Tenant(uuid.UUID(int=1), "default", "Test campground", "public")
    with django_db_blocker.unblock():
        connection.ensure_connection()
        raw = connection.connection
        prepare_registry(raw)
        raw.execute(
            "SELECT "
            "set_config('search_path','public,campground_extensions,pg_catalog',false), "
            "set_config('app.tenant',%s,false)",
            [str(tenant.id)],
        )
        raw.execute(
            "INSERT INTO public.campground_tenants(id,slug,name,schema_name,active) "
            "VALUES (%s,%s,%s,%s,true) ON CONFLICT DO NOTHING",
            [tenant.id, tenant.slug, tenant.name, tenant.schema],
        )
        protect_schema(raw, tenant.id, tenant.schema, grant=False)
    token = _current.set(tenant)
    try:
        yield from original.__wrapped__(request, django_db_setup, django_db_blocker)
    finally:
        _current.reset(token)
        with django_db_blocker.unblock():
            if connection.connection is not None:
                connection.connection.execute(
                    "SELECT set_config('app.tenant','',false), "
                    "set_config('search_path','public,pg_catalog',false)"
                )
