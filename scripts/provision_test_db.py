"""Provision only the isolated loopback test database; no secrets printed."""

import os
from pathlib import Path

import psycopg
from psycopg import sql


def main():
    root = Path(__file__).resolve().parents[1]
    with psycopg.connect(
        host="127.0.0.1",
        port=int(os.environ.get("TEST_DATABASE_PORT", "55432")),
        dbname="campground_test",
        user="postgres",
        password=(root / ".secrets/admin_password").read_text(),
        autocommit=True,
    ) as conn:
        # This identity creates/drops disposable pytest databases. It is never the
        # deployment runtime identity and cannot administer roles or bypass RLS.
        if not conn.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s", ("campground_test_runner",)
        ).fetchone():
            conn.execute(
                sql.SQL(
                    "CREATE ROLE campground_test_runner LOGIN CREATEDB NOSUPERUSER NOCREA"
                    "TEROLE PASSWORD {}"
                ).format(sql.Literal((root / ".secrets/database_password").read_text()))
            )
        conn.execute("ALTER DATABASE campground_test OWNER TO campground_test_runner")
        conn.execute("REVOKE ALL ON DATABASE campground_test FROM PUBLIC")
        if not conn.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", ["campground_test_template"]
        ).fetchone():
            conn.execute("CREATE DATABASE campground_test_template OWNER campground_test_runner")
    with psycopg.connect(
        host="127.0.0.1",
        port=int(os.environ.get("TEST_DATABASE_PORT", "55432")),
        dbname="campground_test_template",
        user="postgres",
        password=(root / ".secrets/admin_password").read_text(),
        autocommit=True,
    ) as template:
        template.execute("CREATE SCHEMA IF NOT EXISTS campground_extensions")
        template.execute(
            "CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA campground_extensions"
        )
        template.execute("GRANT USAGE ON SCHEMA campground_extensions TO campground_test_runner")
    print(
        "Isolated test database and extension template provisioned; "
        "test role remains non-superuser."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(
            "Test database provisioning failed; no credentials are displayed."
        ) from None
