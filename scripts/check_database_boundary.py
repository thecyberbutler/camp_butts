"""Run inside the web container; check real runtime grants without retaining writes."""

import argparse
import sys

import django
from django.db import DatabaseError, connection, transaction
from psycopg import sql


def check_role():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_user, rolsuper, rolcreatedb, rolcreaterole, "
            "rolreplication, rolbypassrls "
            "FROM pg_roles WHERE rolname = current_user"
        )
        if cursor.fetchone() != ("campground_app", False, False, False, False, False):
            raise RuntimeError("Unexpected runtime role")
    probes = (
        "CREATE TABLE public.campground_boundary_probe (id integer)",
        "UPDATE audit_event SET action = action WHERE false",
        "DELETE FROM audit_event WHERE false",
        "SELECT 1 FROM django_migrations LIMIT 0",
        "SELECT 1 FROM public.campground_tenant_events LIMIT 0",
        "UPDATE public.campground_tenants SET active=active WHERE false",
        "SELECT nextval('public.campground_tenant_events_id_seq')",
    )
    for statement in probes:
        denied = False
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(statement)
                transaction.set_rollback(True)
        except DatabaseError as error:
            if getattr(error.__cause__, "sqlstate", None) != "42501":
                raise RuntimeError("Unexpected boundary probe failure") from None
            denied = True
        if not denied:
            raise RuntimeError("Runtime boundary did not deny a protected operation")
    print("Runtime database boundary verified; all protected operations denied.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campground", required=True)
    parser.add_argument("--other-campground")
    options = parser.parse_args()
    try:
        django.setup()
        from apps.tenancy.context import lookup, tenant_scope

        tenant = lookup(options.campground)
        if tenant is None:
            raise RuntimeError("Select an active campground")
        with tenant_scope(tenant):
            check_role()
            if options.other_campground:
                other = lookup(options.other_campground)
                if other is None or other.id == tenant.id:
                    raise RuntimeError("Select a distinct active campground")
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql.SQL("SELECT count(*) FROM {}.configuration_campground").format(
                            sql.Identifier(other.schema)
                        )
                    )
                    if cursor.fetchone()[0] != 0:
                        raise RuntimeError("Cross-tenant row disclosure")
                denied = False
                try:
                    with transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(
                            sql.SQL(
                                "INSERT INTO {}.campsites_amenity (name) VALUES ('boundary-probe')"
                            ).format(sql.Identifier(other.schema))
                        )
                        transaction.set_rollback(True)
                except DatabaseError as error:
                    denied = getattr(error.__cause__, "sqlstate", None) == "42501"
                if not denied:
                    raise RuntimeError("Cross-tenant insert not denied")
                print("Runtime cross-schema read/write isolation verified.")
    except Exception:
        # Never render driver errors, settings or connection credentials.
        print("Database boundary validation failed; no credentials displayed.", file=sys.stderr)
        raise SystemExit(1) from None
