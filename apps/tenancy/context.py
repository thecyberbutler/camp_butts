"""Explicit tenant scope, with transaction-local PostgreSQL isolation."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.urls import get_script_prefix, set_script_prefix
from psycopg.pq import TransactionStatus

_current = ContextVar("campground_tenant", default=None)


@dataclass(frozen=True)
class Tenant:
    id: UUID
    slug: str
    name: str
    schema: str
    active: bool = True


def current_tenant():
    tenant = _current.get()
    if tenant is None:
        raise PermissionDenied("Select a campground before accessing its data.")
    return tenant


def lookup(slug, *, include_inactive=False):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, slug, name, schema_name, active FROM public.campground_tenants "
            "WHERE slug = %s AND (active OR %s)",
            [slug, include_inactive],
        )
        row = cursor.fetchone()
    return Tenant(*row) if row else None


def directory():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT slug, name FROM public.campground_tenants WHERE active ORDER BY name"
        )
        return cursor.fetchall()


@contextmanager
def tenant_scope(tenant, *, urls=False):
    if tenant.schema != "public" and tenant.schema != "tenant_" + tenant.id.hex:
        raise PermissionDenied("Invalid campground schema binding.")
    token = _current.set(tenant)
    previous_prefix = get_script_prefix()
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT current_setting('search_path'), current_setting('app.tenant', true)"
                )
                old_path, old_tenant = cursor.fetchone()
                # No public fallback: another campground's tables must never resolve.
                path = f'"{tenant.schema}", campground_extensions, pg_catalog'
                cursor.execute(
                    "SELECT set_config('search_path', %s, true), set_config('app.tenant', "
                    "%s, true)",
                    [path, str(tenant.id)],
                )
            if urls:
                set_script_prefix(f"/c/{tenant.slug}/")
            try:
                yield tenant
            finally:
                # Savepoint rollback restores SET LOCAL itself. On normal exit also
                # restore nested scopes before control returns to their caller.
                if (
                    not connection.needs_rollback
                    and connection.connection.info.transaction_status != TransactionStatus.INERROR
                ):
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT set_config('search_path', %s, true), set_config('app.tenant', "
                            "%s, true)",
                            [old_path, old_tenant or ""],
                        )
    finally:
        set_script_prefix(previous_prefix)
        _current.reset(token)
