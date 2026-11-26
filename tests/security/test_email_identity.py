import uuid
from contextlib import contextmanager
from datetime import timedelta

import pytest
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client
from django.utils import timezone
from psycopg import sql

from apps.accounts.models import User
from apps.tenancy.context import Tenant, tenant_scope

pytestmark = pytest.mark.django_db


def test_no_usernames_or_blank_email_and_manager_validation(client, password):
    with pytest.raises(FieldDoesNotExist):
        User._meta.get_field("username")
    for endpoint in ("login", "signup"):
        response = client.get(f"/c/default/accounts/{endpoint}/", secure=True)
        assert b'name="username"' not in response.content
    with pytest.raises(ValidationError):
        User.objects.create_user(email="", password=password)
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(email="")
    user = User.objects.create_user(email="Mixed@Example.Test", password=password)
    assert user.email == "mixed@example.test"
    assert user.get_username() == user.email
    with pytest.raises(TypeError):
        User.objects.create_user(email="another@example.test", username="obsolete")


def test_email_login_rate_limit_applies_across_ip_and_case(camper, password):
    for index in range(5):
        Client().post(
            "/c/default/accounts/login/",
            {"login": camper.email.upper(), "password": "synthetic-wrong-password"},
            REMOTE_ADDR=f"192.0.2.{index + 1}",
            secure=True,
        )
    browser = Client()
    browser.post(
        "/c/default/accounts/login/",
        {"login": camper.email, "password": password},
        REMOTE_ADDR="192.0.2.99",
        secure=True,
    )
    assert "_auth_user_id" not in browser.session


@contextmanager
def legacy_schema():
    identity = uuid.uuid4()
    tenant = Tenant(identity, "migration-review", "Migration review", "tenant_" + identity.hex)
    with connection.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(tenant.schema)))
    try:
        with tenant_scope(tenant):
            executor = MigrationExecutor(connection)
            targets = [
                (app, "0002_alter_user_options") if app == "accounts" else (app, name)
                for app, name in executor.loader.graph.leaf_nodes()
            ]
            executor.migrate(targets)
            yield executor.loader.project_state(targets).apps
    finally:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(tenant.schema)))


def test_existing_identity_migration_preserves_account_and_lockout(password):
    from axes.handlers.proxy import AxesProxyHandler
    from django.test import RequestFactory

    with legacy_schema() as old:
        legacy = old.get_model("accounts", "User").objects.create(
            username="legacy-handle",
            email="Legacy@Example.Test",
            approved=True,
        )
        # Preserve the existing password bytes and immutable PK, not a newly issued credential.
        from django.contrib.auth.hashers import make_password

        encoded = make_password(password)
        old.get_model("accounts", "User").objects.filter(pk=legacy.pk).update(password=encoded)
        old.get_model("account", "EmailAddress").objects.create(
            user_id=legacy.pk,
            email=legacy.email.lower(),
            primary=True,
            verified=True,
        )
        old.get_model("axes", "AccessAttempt").objects.create(
            username="legacy-handle",
            ip_address="192.0.2.1",
            user_agent="test",
            failures_since_start=5,
            get_data="",
            post_data="",
            http_accept="",
            path_info="",
        )
        old.get_model("sessions", "Session").objects.create(
            session_key=uuid.uuid4().hex,
            session_data="synthetic",
            expire_date=timezone.now() + timedelta(hours=1),
        )
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        MigrationExecutor(connection).migrate([("accounts", "0003_email_identity")])
        current = User.objects.get(pk=legacy.pk)
        assert current.email == "legacy@example.test" and current.approved
        assert (
            current.password == encoded and current.security_version == legacy.security_version + 1
        )
        from django.contrib.sessions.models import Session

        assert not Session.objects.exists()
        request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.99")
        request.axes_attempt_time = timezone.now()
        request.axes_ip_address = "192.0.2.99"
        request.axes_user_agent = "different"
        assert not AxesProxyHandler.is_allowed(request, {"email": current.email})
        assert (
            old.get_model("axes", "AccessAttempt").objects.filter(username="legacy-handle").exists()
        )


@pytest.mark.parametrize("email", ["", "not-an-email"])
def test_invalid_legacy_email_stops_migration_without_deleting_identity(email):
    with legacy_schema() as old:
        user = old.get_model("accounts", "User").objects.create(username="legacy", email=email)
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with (
            pytest.raises(RuntimeError, match="Review invalid account email"),
            transaction.atomic(),
        ):
            MigrationExecutor(connection).migrate([("accounts", "0003_email_identity")])
        assert old.get_model("accounts", "User").objects.get(pk=user.pk).username == "legacy"


def test_username_login_is_rejected_even_with_correct_password(client, camper, password):
    response = client.post(
        "/c/default/accounts/login/", {"login": "camper", "password": password}, secure=True
    )
    assert response.status_code == 200 and "_auth_user_id" not in client.session


def test_migration_and_model_state_match():
    from io import StringIO

    from django.core.management import call_command

    call_command("makemigrations", check=True, dry_run=True, stdout=StringIO())


def test_colliding_normalization_aborts_before_changing_accounts():
    with legacy_schema() as old:
        LegacyUser = old.get_model("accounts", "User")
        LegacyUser.objects.create(username="first", email="same@straße.test")
        LegacyUser.objects.create(username="second", email="same@strasse.test")
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with pytest.raises(RuntimeError, match="Review colliding"), transaction.atomic():
            MigrationExecutor(connection).migrate([("accounts", "0003_email_identity")])
        assert LegacyUser.objects.count() == 2
        assert set(LegacyUser.objects.values_list("username", flat=True)) == {"first", "second"}


def test_secondary_email_requires_review_before_migration():
    with legacy_schema() as old:
        user = old.get_model("accounts", "User").objects.create(
            username="legacy", email="primary@example.test"
        )
        old.get_model("account", "EmailAddress").objects.create(
            user_id=user.pk, email="secondary@example.test", primary=False, verified=False
        )
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        with pytest.raises(RuntimeError, match="Review secondary"), transaction.atomic():
            MigrationExecutor(connection).migrate([("accounts", "0003_email_identity")])
        assert old.get_model("accounts", "User").objects.get(pk=user.pk).username == "legacy"
