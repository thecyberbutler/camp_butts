"""Controlled one-shot database provisioning; credentials never leave this process."""

import argparse
from pathlib import Path

import psycopg
from psycopg import sql


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--grant-runtime", action="store_true")
    options = parser.parse_args()
    root = Path("/run/secrets")
    with psycopg.connect(
        host="db",
        dbname="campground",
        user="postgres",
        password=(root / "admin_password").read_text().strip(),
        autocommit=True,
    ) as conn:
        conn.execute("SET log_statement = 'none'")
        conn.execute("SET log_min_error_statement = 'panic'")
        if options.grant_runtime:
            conn.execute(Path("/app/scripts/runtime_grants.sql").read_text())
        else:
            conn.execute("REVOKE ALL ON DATABASE campground FROM PUBLIC")
            conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            for role, filename in [
                ("campground_migrator", "migration_password"),
                ("campground_app", "database_password"),
            ]:
                if not conn.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)
                ).fetchone():
                    conn.execute(
                        sql.SQL(
                            "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                            "NOREPLICATION PASSWORD {}"
                        ).format(
                            sql.Identifier(role), sql.Literal((root / filename).read_text().strip())
                        )
                    )
            conn.execute(
                "GRANT CONNECT ON DATABASE campground TO campground_migrator, campground_app"
            )
            conn.execute("GRANT USAGE, CREATE ON SCHEMA public TO campground_migrator")
            conn.execute("GRANT USAGE ON SCHEMA public TO campground_app")
            conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    print("Database provisioning step completed; no credentials displayed.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(
            "Database provisioning failed. Check protected configuration; no credentials displayed."
        ) from None
