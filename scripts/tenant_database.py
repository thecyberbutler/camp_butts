"""Operator-only schema provisioning. SQL identifiers never come from URL input."""

import re
import uuid

from psycopg import sql

REGISTRY = """
CREATE TABLE IF NOT EXISTS public.campground_tenants (
 id uuid PRIMARY KEY,
 slug varchar(63) NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
 name varchar(120) NOT NULL,
 schema_name varchar(63) NOT NULL UNIQUE,
 active boolean NOT NULL DEFAULT false,
 CHECK (schema_name = 'public' OR schema_name = 'tenant_' || replace(id::text, '-', ''))
)
"""


def prepare_registry(conn):
    conn.execute(REGISTRY)
    conn.execute("REVOKE ALL ON public.campground_tenants FROM PUBLIC")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS public.campground_tenant_events (id bigint "
        "GENERATED ALWAYS AS IDENTITY PRIMARY KEY, tenant_id uuid NOT NULL, "
        "action varchar(24) NOT NULL, created_at timestamptz NOT NULL DEFAULT now())"
    )
    conn.execute("REVOKE ALL ON public.campground_tenant_events FROM PUBLIC")
    conn.execute("CREATE SCHEMA IF NOT EXISTS campground_extensions")
    row = conn.execute(
        "SELECT n.nspname FROM pg_extension e JOIN pg_namespace n ON "
        "n.oid=e.extnamespace WHERE e.extname='btree_gist'"
    ).fetchone()
    if row and row[0] != "campground_extensions":
        conn.execute("ALTER EXTENSION btree_gist SET SCHEMA campground_extensions")


def register(conn, slug, name, *, adopt=False):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 63:
        raise ValueError("Invalid campground slug")
    if not name.strip() or len(name) > 120:
        raise ValueError("Invalid campground name")
    tenant_id = uuid.uuid4()
    schema = "public" if adopt else "tenant_" + tenant_id.hex
    if not adopt:
        conn.execute(
            sql.SQL("CREATE SCHEMA {} AUTHORIZATION campground_migrator").format(
                sql.Identifier(schema)
            )
        )
    conn.execute(
        "INSERT INTO public.campground_tenants (id, slug, name, schema_name) VALUES (%s,%s,%s,%s)",
        [tenant_id, slug, name, schema],
    )
    conn.execute(
        "INSERT INTO public.campground_tenant_events(tenant_id,action) VALUES (%s,'registered')",
        [tenant_id],
    )
    return tenant_id, schema


def protect_schema(conn, tenant_id, schema, *, grant=True):
    tables = conn.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = %s AND tablename NOT IN "
        "('campground_tenants', 'campground_tenant_events')",
        [schema],
    ).fetchall()
    required = {
        "accounts_user",
        "configuration_campground",
        "reservations_occupancy",
        "audit_event",
        "django_session",
        "mfa_authenticator",
        "security_cache",
    }
    if not required.issubset({row[0] for row in tables}):
        raise ValueError("Complete campground migrations before applying runtime grants")
    for (table,) in tables:
        target = sql.Identifier(schema, table)
        conn.execute(sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(target))
        conn.execute(sql.SQL("ALTER TABLE {} FORCE ROW LEVEL SECURITY").format(target))
        # A restrictive guard still applies if a future permissive policy is added.
        for policy, mode in (("tenant_boundary", "PERMISSIVE"), ("tenant_guard", "RESTRICTIVE")):
            exists = conn.execute(
                "SELECT 1 FROM pg_policies WHERE schemaname=%s AND tablename=%s AND policyname=%s",
                [schema, table, policy],
            ).fetchone()
            if exists:
                statement = sql.SQL("ALTER POLICY {} ON {} USING ").format(
                    sql.Identifier(policy), target
                )
            else:
                statement = sql.SQL("CREATE POLICY {} ON {} AS {} USING ").format(
                    sql.Identifier(policy), target, sql.SQL(mode)
                )
            conn.execute(
                statement
                + sql.SQL(
                    "(current_setting('app.tenant', true) = {}) WITH CHECK "
                    "(current_setting('app.tenant', true) = {})"
                ).format(sql.Literal(str(tenant_id)), sql.Literal(str(tenant_id)))
            )
        if grant:
            conn.execute(sql.SQL("REVOKE ALL ON {} FROM campground_app").format(target))
            if table == "socialaccount_socialtoken":
                # Django's account deletion collector checks/deletes dependent rows.
                # Never permit token creation or modification, even if settings drift.
                conn.execute(sql.SQL("GRANT SELECT, DELETE ON {} TO campground_app").format(target))
            if table not in {
                "django_migrations",
                "socialaccount_socialapp",
                "socialaccount_socialapp_sites",
                "socialaccount_socialtoken",
            }:
                privileges = (
                    sql.SQL("SELECT, INSERT")
                    if table == "audit_event"
                    else sql.SQL("SELECT, INSERT, UPDATE, DELETE")
                )
                conn.execute(sql.SQL("GRANT {} ON {} TO campground_app").format(privileges, target))
    if grant:
        conn.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO campground_app").format(sql.Identifier(schema))
        )
        sequences = conn.execute(
            "SELECT sequencename FROM pg_sequences WHERE schemaname=%s AND "
            "sequencename <> 'campground_tenant_events_id_seq'",
            [schema],
        ).fetchall()
        for (sequence,) in sequences:
            if sequence.startswith(("socialaccount_socialapp", "socialaccount_socialtoken")):
                conn.execute(
                    sql.SQL("REVOKE ALL ON {} FROM campground_app").format(
                        sql.Identifier(schema, sequence)
                    )
                )
                continue
            conn.execute(
                sql.SQL("GRANT USAGE, SELECT ON {} TO campground_app").format(
                    sql.Identifier(schema, sequence)
                )
            )
        # These are platform operator records, never ordinary campground data.
        conn.execute(
            "REVOKE ALL ON public.campground_tenant_events FROM campground_app, campground_migrator"
        )
        conn.execute(
            "REVOKE ALL ON SEQUENCE public.campground_tenant_events_id_seq "
            "FROM campground_app, campground_migrator"
        )
        conn.execute(
            "GRANT SELECT ON public.campground_tenants TO campground_app, campground_migrator"
        )
        conn.execute(
            "GRANT USAGE ON SCHEMA public, campground_extensions TO campground_app, "
            "campground_migrator"
        )
