import uuid
from io import StringIO

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import DatabaseError, connection, transaction
from django.test import Client
from django.urls import reverse
from psycopg import sql

from apps.accounts.models import User
from apps.campsites.models import Campsite, CampsiteType
from apps.configuration.models import Campground
from apps.notifications.models import Notification
from apps.reservations.models import Occupancy
from apps.reservations.services import book
from apps.tenancy.context import Tenant, current_tenant, tenant_scope
from config.sessions import SessionStore
from scripts.tenant_database import protect_schema

pytestmark = pytest.mark.django_db


@pytest.fixture
def second_tenant(password):
    tenant_id = uuid.uuid4()
    tenant = Tenant(tenant_id, "second", "Second campground", "tenant_" + tenant_id.hex)
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(tenant.schema)))
        cursor.execute(
            "INSERT INTO public.campground_tenants VALUES (%s,%s,%s,%s,true)",
            [tenant.id, tenant.slug, tenant.name, tenant.schema],
        )
    with tenant_scope(tenant):
        call_command("migrate", interactive=False, verbosity=0, stdout=StringIO())
        call_command("setup_roles", stdout=StringIO())
        Campground.objects.filter(pk=1).update(name=tenant.name)
        User.objects.create_user(
            username="camper", email="camper@example.test", password=password, approved=True
        )
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        protect_schema(connection.connection, tenant.id, tenant.schema, grant=False)
    yield tenant
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(tenant.schema)))
        cursor.execute("DELETE FROM public.campground_tenants WHERE id=%s", [tenant.id])


def test_selector_is_explicit_and_rejects_conflicting_or_unknown_context(second_tenant):
    client = Client()
    response = client.get("/?campground=second", secure=True)
    assert response.status_code == 302 and response.url == "/c/second/"
    for path in ("/accounts/login/", "/c/missing/", "/?campground=missing"):
        assert client.get(path, secure=True).status_code == 404
    for path in (
        "/?campground=second&campground=default",
        "/?campground=../public",
        "/c/second/?campground=default",
    ):
        assert client.get(path, secure=True).status_code == 400
    assert client.post("/?campground=second", {}, secure=True).status_code == 400
    assert b"Second campground" in client.get("/c/second/", secure=True).content
    assert b"/c/second/accounts/login/" in client.get("/c/second/", secure=True).content


def test_accounts_with_same_identifiers_are_separate_and_sessions_do_not_cross(
    camper, second_tenant, password
):
    client = Client()
    response = client.post(
        "/c/default/accounts/login/", {"login": "camper", "password": password}, secure=True
    )
    assert response.status_code == 302 and response.url == "/c/default/dashboard/"
    assert client.get("/c/default/dashboard/", secure=True).status_code == 200
    assert client.get("/c/second/dashboard/", secure=True).status_code == 302
    response = client.post(
        "/c/second/accounts/login/", {"login": "camper", "password": password}, secure=True
    )
    assert response.status_code == 302 and response.url == "/c/second/dashboard/"
    assert client.get("/c/second/dashboard/", secure=True).status_code == 200
    assert client.get("/c/default/dashboard/", secure=True).status_code == 302
    with tenant_scope(second_tenant):
        assert User.objects.get(username="camper").pk != camper.pk


def test_qualified_cross_schema_reads_and_writes_fail_closed(camper, second_tenant):
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("SELECT count(*) FROM {}.accounts_user").format(
                sql.Identifier(second_tenant.schema)
            )
        )
        assert cursor.fetchone()[0] == 0
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("INSERT INTO {}.campsites_amenity (name) VALUES ('cross-tenant')").format(
                sql.Identifier(second_tenant.schema)
            )
        )
    with tenant_scope(second_tenant), connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM public.accounts_user")
        assert cursor.fetchone()[0] == 0
        cursor.execute("UPDATE public.accounts_user SET first_name='cross-tenant'")
        assert cursor.rowcount == 0
    camper.refresh_from_db()
    assert camper.first_name != "cross-tenant"


def test_absent_database_tenant_context_denies_even_schema_owner(camper):
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.tenant','',true)")
        assert User.objects.count() == 0
        with pytest.raises(DatabaseError), transaction.atomic():
            User.objects.create_user(username="unscoped", email="none@example.test")
        transaction.set_rollback(True)
    assert User.objects.filter(pk=camper.pk).exists()


def test_sessions_remain_bound_when_ciphertext_is_copied(second_tenant):
    encoded = SessionStore().encode({"synthetic": "session payload"})
    with tenant_scope(second_tenant):
        denied = SessionStore().decode(encoded) == {}
        assert denied


def test_reservations_notifications_and_staff_do_not_cross(
    booking, browser, second_tenant, password
):
    notification = Notification.objects.create(
        recipient=booking.camper, message="Only first campground"
    )
    with tenant_scope(second_tenant):
        assert not Occupancy.objects.exists()
        assert not Notification.objects.exists()
        user = User.objects.get(username="camper")
        assert not user.has_perm("reservations.operate_reservations")
    assert browser.get(f"/c/second/reservations/{booking.pk}/", secure=True).status_code == 302
    assert browser.get("/c/second/operations/", secure=True).status_code == 302
    second_browser = Client()
    response = second_browser.post(
        "/c/second/accounts/login/", {"login": "camper", "password": password}, secure=True
    )
    assert response.status_code == 302
    assert (
        second_browser.get(f"/c/second/reservations/{booking.pk}/", secure=True).status_code == 404
    )
    assert (
        second_browser.post(
            f"/c/second/notifications/{notification.pk}/read/", {}, secure=True
        ).status_code
        == 404
    )
    assert second_browser.get("/c/second/operations/", secure=True).status_code == 403


def test_content_type_cache_does_not_cross_schemas(second_tenant):
    original = ContentType.objects.get_for_model(User)
    with tenant_scope(second_tenant):
        other = ContentType.objects.create(app_label="synthetic", model="probe")
        assert ContentType.objects.get_for_id(other.pk).app_label == "synthetic"
    assert ContentType.objects.get_for_model(User).pk == original.pk
    with pytest.raises(ContentType.DoesNotExist):
        ContentType.objects.get_for_id(other.pk)


def test_nested_scope_and_error_restore_database_and_url_context(second_tenant):
    before = current_tenant()
    with pytest.raises(ValueError):
        with tenant_scope(second_tenant, urls=True):
            assert reverse("home") == "/c/second/"
            assert Campground.current().name == second_tenant.name
            raise ValueError("synthetic failure")
    assert current_tenant() == before
    assert Campground.current().name != second_tenant.name
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('app.tenant')")
        assert cursor.fetchone()[0] == str(before.id)


def test_booking_same_site_identifier_and_dates_is_independent(camper, site, dates, second_tenant):
    first = book(
        actor=camper, campsite_id=site.pk, start=dates[0], end=dates[1], submission_key=uuid.uuid4()
    )
    with tenant_scope(second_tenant):
        kind = CampsiteType.objects.create(name="Tent")
        Campsite.objects.create(id=site.pk, name=site.name, site_type=kind)
        user = User.objects.get(username="camper")
        second = book(
            actor=user,
            campsite_id=site.pk,
            start=dates[0],
            end=dates[1],
            submission_key=uuid.uuid4(),
        )
        assert second.pk != first.pk
        assert Occupancy.objects.count() == 1
    assert Occupancy.objects.count() == 1


def test_disabling_tenant_denies_existing_sessions(browser):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE public.campground_tenants SET active=false WHERE slug='default'")
    assert browser.get("/c/default/dashboard/", secure=True).status_code == 404


@pytest.mark.django_db(transaction=True)
@pytest.mark.concurrency
def test_simultaneous_tenants_keep_connections_and_inventory_separate(
    camper, site, dates, second_tenant
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    first_tenant = current_tenant()
    with tenant_scope(second_tenant):
        kind = CampsiteType.objects.create(name="Tent")
        Campsite.objects.create(id=site.pk, name=site.name, site_type=kind)
    barrier = Barrier(2)

    def reserve(tenant):
        close_old_connections()
        try:
            with tenant_scope(tenant):
                user = User.objects.get(username="camper")
                barrier.wait(timeout=10)
                item = book(
                    actor=user,
                    campsite_id=site.pk,
                    start=dates[0],
                    end=dates[1],
                    submission_key=uuid.uuid4(),
                )
                return item.pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        reservations = list(pool.map(reserve, [first_tenant, second_tenant]))
    assert len(set(reservations)) == 2
    assert Occupancy.objects.count() == 1
    with tenant_scope(second_tenant):
        assert Occupancy.objects.count() == 1


def test_restrictive_guard_survives_additional_permissive_policy(second_tenant):
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL(
                "CREATE POLICY synthetic_permissive ON {}.accounts_user "
                "USING (true) WITH CHECK (true)"
            ).format(sql.Identifier(second_tenant.schema))
        )
        cursor.execute(
            sql.SQL("SELECT count(*) FROM {}.accounts_user").format(
                sql.Identifier(second_tenant.schema)
            )
        )
        assert cursor.fetchone()[0] == 0


def test_platform_operator_tables_are_not_campground_tables():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_policies WHERE schemaname='public' "
            "AND tablename IN ('campground_tenants', 'campground_tenant_events')"
        )
        assert cursor.fetchone()[0] == 0


def test_email_confirmation_tokens_are_bound_to_campground(camper, second_tenant):
    from allauth.account.models import EmailAddress, EmailConfirmationHMAC

    address = EmailAddress.objects.create(pk=501, user=camper, email=camper.email)
    token = EmailConfirmationHMAC(address).key
    with tenant_scope(second_tenant):
        user = User.objects.get(username="camper")
        EmailAddress.objects.create(pk=501, user=user, email=user.email)
        rejected = EmailConfirmationHMAC.from_key(token) is None
        assert rejected
    accepted = EmailConfirmationHMAC.from_key(token) is not None
    assert accepted


def test_password_reset_tokens_are_bound_even_for_identical_restored_accounts(
    camper, second_tenant
):
    from allauth.account.forms import default_token_generator

    token = default_token_generator.make_token(camper)
    with tenant_scope(second_tenant):
        User.objects.all().delete()
        cloned = User.objects.create(
            pk=camper.pk,
            username=camper.username,
            email=camper.email,
            password=camper.password,
            last_login=camper.last_login,
        )
        rejected = not default_token_generator.check_token(cloned, token)
        assert rejected
    accepted = default_token_generator.check_token(camper, token)
    assert accepted


def test_management_command_requires_known_campground(second_tenant):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("tenant_command", "--campground", "unknown", "setup_roles", stdout=StringIO())
    call_command("tenant_command", "--campground", "second", "setup_roles", stdout=StringIO())
    assert current_tenant().slug == "default"


def test_security_cache_and_totp_issuer_are_scoped(second_tenant):
    from allauth.mfa import app_settings
    from django.core.cache import cache

    first_issuer = app_settings.TOTP_ISSUER
    cache.set("synthetic_limit", 5)
    with tenant_scope(second_tenant):
        assert cache.get("synthetic_limit") is None
        cache.set("synthetic_limit", 1)
        assert app_settings.TOTP_ISSUER != first_issuer
    assert cache.get("synthetic_limit") == 5


def test_failed_logins_do_not_lock_other_campgrounds(camper, second_tenant, password):
    import secrets

    client = Client()
    for _ in range(5):
        client.post(
            "/c/default/accounts/login/",
            {"login": "camper", "password": secrets.token_urlsafe(32)},
            secure=True,
        )
    response = client.post(
        "/c/second/accounts/login/", {"login": "camper", "password": password}, secure=True
    )
    assert response.status_code == 302 and response.url == "/c/second/dashboard/"


def test_invitation_from_another_campground_is_not_accepted(camper, second_tenant, password):
    import hashlib
    import secrets
    from datetime import timedelta

    from django.utils import timezone

    from apps.accounts.models import Invitation

    invitation = secrets.token_urlsafe(32)
    Invitation.objects.create(
        digest=hashlib.sha256(invitation.encode()).hexdigest(),
        expires_at=timezone.now() + timedelta(days=1),
        created_by=camper,
    )
    with tenant_scope(second_tenant):
        Campground.objects.filter(pk=1).update(registration_mode="invitation")
    response = Client().post(
        "/c/second/accounts/signup/",
        {
            "username": "newcamper",
            "email": "newcamper@example.test",
            "password1": password,
            "password2": password,
            "invitation": invitation,
            "first_name": "New",
            "last_name": "Camper",
            "rules_agreed": "on",
            "policies_agreed": "on",
            "phone": "",
        },
        secure=True,
    )
    # Uniform signup responses may hide why signup failed; the DB is authoritative.
    assert response.status_code == 302
    with tenant_scope(second_tenant):
        assert not User.objects.filter(username="newcamper").exists()
    assert Invitation.objects.get(created_by=camper).uses == 0
