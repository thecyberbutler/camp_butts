"""Controlled one-shot database provisioning; credentials never leave this process."""

import argparse
from pathlib import Path

import psycopg
from psycopg import sql
from tenant_database import prepare_registry, protect_schema, register


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grant-runtime", action="store_true")
    parser.add_argument("--campground")
    parser.add_argument("--create-campground")
    parser.add_argument("--name")
    parser.add_argument("--adopt-existing", action="store_true")
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--deactivate", action="store_true")
    options = parser.parse_args()
    if (
        sum(
            bool(value)
            for value in (options.create_campground, options.grant_runtime, options.deactivate)
        )
        > 1
    ):
        parser.error("Select only one provisioning operation")
    if options.adopt_existing and not options.create_campground:
        parser.error("Adoption requires --create-campground")
    if options.activate and not options.grant_runtime:
        parser.error("Activation requires --grant-runtime")
    if options.name and not options.create_campground:
        parser.error("Display name requires --create-campground")
    if bool(options.campground) != bool(options.grant_runtime or options.deactivate):
        parser.error("Grant/deactivation requires an explicit --campground")
    root = Path("/run/secrets")
    with psycopg.connect(
        host="db",
        dbname="campground",
        user="postgres",
        password=(root / "admin_password").read_text().strip(),
        autocommit=False,
    ) as conn:
        conn.execute("SET log_statement = 'none'")
        conn.execute("SET log_min_error_statement = 'panic'")
        conn.execute("REVOKE ALL ON DATABASE campground FROM PUBLIC")
        conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        for role, filename in [
            ("campground_migrator", "migration_password"),
            ("campground_app", "database_password"),
        ]:
            if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone():
                conn.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                        "NOREPLICATION NOBYPASSRLS PASSWORD {}"
                    ).format(
                        sql.Identifier(role), sql.Literal((root / filename).read_text().strip())
                    )
                )
            attributes = conn.execute(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname=%s",
                [role],
            ).fetchone()
            if attributes != (False, False, False, False, False):
                raise ValueError("Existing database role violates least-privilege requirements")
            if conn.execute(
                "SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member "
                "WHERE r.rolname=%s LIMIT 1",
                [role],
            ).fetchone():
                raise ValueError("Application identities must not inherit other database roles")
        conn.execute("GRANT CONNECT ON DATABASE campground TO campground_migrator, campground_app")
        conn.execute("GRANT USAGE, CREATE ON SCHEMA public TO campground_migrator")
        conn.execute("GRANT USAGE ON SCHEMA public TO campground_app")
        conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        prepare_registry(conn)
        conn.execute(
            "GRANT SELECT ON public.campground_tenants TO campground_app, campground_migrator"
        )
        conn.execute(
            "GRANT USAGE ON SCHEMA campground_extensions TO campground_migrator, campground_app"
        )
        if options.create_campground:
            if not options.name:
                raise ValueError("Campground display name required")
            tenant_id, schema = register(
                conn, options.create_campground, options.name, adopt=options.adopt_existing
            )
            if options.adopt_existing:
                protect_schema(conn, tenant_id, schema)
        if options.deactivate:
            if not options.campground:
                raise ValueError("Select the campground explicitly")
            changed = conn.execute(
                "UPDATE public.campground_tenants SET active=false WHERE slug=%s RETURNING id",
                [options.campground],
            ).fetchone()
            if not changed:
                raise ValueError("Unknown campground")
            conn.execute(
                "INSERT INTO public.campground_tenant_events(tenant_id,action) SELECT "
                "id,'deactivated' FROM public.campground_tenants WHERE slug=%s",
                [options.campground],
            )
        if options.grant_runtime:
            if not options.campground:
                raise ValueError("Select the campground explicitly")
            row = conn.execute(
                "SELECT id, schema_name FROM public.campground_tenants WHERE slug=%s FOR UPDATE",
                [options.campground],
            ).fetchone()
            if not row:
                raise ValueError("Unknown campground")
            protect_schema(conn, *row)
            if options.activate:
                # Initialize new tenant branding only once; preserve adopted/custom branding.
                if row[1] != "public":
                    conn.execute(
                        sql.SQL(
                            "UPDATE {}.configuration_campground SET name = "
                            "(SELECT name FROM public.campground_tenants WHERE id=%s) "
                            "WHERE id=1 AND name='Campground' AND NOT EXISTS "
                            "(SELECT 1 FROM public.campground_tenant_events WHERE tenant_id=%s "
                            "AND action='activated')"
                        ).format(sql.Identifier(row[1])),
                        [row[0], row[0]],
                    )
                conn.execute(
                    "INSERT INTO public.campground_tenant_events(tenant_id,action) VALUES "
                    "(%s,'activated')",
                    [row[0]],
                )
                conn.execute(
                    "UPDATE public.campground_tenants SET active=true WHERE slug=%s",
                    [options.campground],
                )
    print("Database provisioning step completed; no credentials displayed.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(
            "Database provisioning failed. Check protected configuration; no credentials displayed."
        ) from None
