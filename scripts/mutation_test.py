"""Run mutmut in a disposable source copy against private synthetic PostgreSQL databases."""

import argparse
import fnmatch
import json
import os
import re
import secrets
import shutil
import signal
import stat

# Reviewed fixed executable, argv and no shell; see SD-024.
import subprocess  # nosec B404
import tempfile
from collections import Counter
from pathlib import Path

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
COPY_ROOTS = (
    "apps",
    "config",
    "templates",
    "static",
    "scripts",
    "tests",
    "infra",
    "data",
    "pyproject.toml",
    "poetry.lock",
    "manage.py",
    "gunicorn.conf.py",
)
# Internal errors, timeouts and missing tests are not accepted as successful kills.
STATUSES = {
    0: "survived",
    1: "killed",
    3: "internal_error",
    5: "no_tests",
    33: "no_tests",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    37: "type_check_only",
    None: "not_checked",
}


def copy_sources(destination):
    for name in COPY_ROOTS:
        source = ROOT / name
        paths = source.rglob("*") if source.is_dir() else [source]
        for path in paths:
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.is_symlink():
                raise ValueError("Symlink in mutation source allowlist")
            if path.is_file():
                target = destination / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)


def summarize(workspace, selector):
    outcomes = {}
    for path in (workspace / "mutants").rglob("*.meta"):
        data = json.loads(path.read_text())
        for name, code in data["exit_code_by_key"].items():
            if fnmatch.fnmatch(name, selector):
                outcomes[name] = STATUSES.get(code, "runner_error")
    return {"selector": selector, "counts": dict(Counter(outcomes.values())), "mutants": outcomes}


def run_process(command, *, cwd, env, timeout):
    # Deliberately discard raw pytest/mutmut failure output: no assertion values,
    # SQL errors, synthetic passwords, session values or captured logs are retained.
    # Fixed local executable and validated selector; see SD-024.
    process = subprocess.Popen(  # nosec B603
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selector", default="apps.reservations.services.x_date_range__mutmut_*")
    parser.add_argument("--port", type=int, default=55433)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if not re.fullmatch(r"apps\.reservations\.services\.[A-Za-z0-9_*]+", args.selector):
        parser.error("Select reservation-service mutants only")
    if not 1024 <= args.port <= 65535 or not 30 <= args.timeout <= 7200:
        parser.error("Use a private test port and a 30–7200 second limit")
    os.umask(0o077)
    password_path = ROOT / ".secrets" / "database_password"
    info = password_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Protected synthetic test database credential required")
    password = password_path.read_text().strip()
    with psycopg.connect(
        host="127.0.0.1",
        port=args.port,
        dbname="campground_test",
        user="campground_test_runner",
        password=password,
        autocommit=True,
    ) as conn:
        row = conn.execute(
            "SELECT current_user,current_database(),rolsuper,rolbypassrls,rolcreaterole "
            "FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        if row != ("campground_test_runner", "campground_test", False, False, False):
            raise ValueError("Unexpected test database identity")
        database = "campground_test_mutation_" + secrets.token_hex(8)
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        try:
            conn.execute(
                sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(database))
            )
            artifact_root = ROOT / ".runtime" / "mutation"
            artifact_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            if (
                (ROOT / ".runtime").is_symlink()
                or artifact_root.is_symlink()
                or artifact_root.stat().st_mode & 0o077
            ):
                raise ValueError("Protected mutation artifact directory required")
            workspace = Path(tempfile.mkdtemp(prefix="run-", dir=artifact_root))
            copy_sources(workspace)
            temporary = workspace / "private"
            temporary.mkdir(mode=0o700)
            credential = temporary / "database_password"
            credential.write_text(password)
            env = {
                "PATH": os.environ["PATH"],
                "HOME": str(Path.home()),
                "LANG": "en_US.UTF-8",
                "PYTHONUTF8": "1",
                "TMPDIR": str(temporary),
                "DJANGO_SETTINGS_MODULE": "config.settings.testing",
                "DATABASE_NAME": database,
                "DATABASE_USER": "campground_test_runner",
                "DATABASE_HOST": "127.0.0.1",
                "DATABASE_PORT": str(args.port),
                "DATABASE_PASSWORD_FILE": str(credential),
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                "PYTEST_PLUGINS": "pytest_django.plugin,pytest_cov.plugin",
            }
            print(
                "Mutation testing started in a private source copy; raw test output is discarded.",
                flush=True,
            )
            try:
                code = run_process(
                    [str(ROOT / ".venv/bin/mutmut"), "run", "--max-children", "1", args.selector],
                    cwd=workspace,
                    env=env,
                    timeout=args.timeout,
                )
                report = summarize(workspace, args.selector)
                report["runner_exit_code"] = code
                (workspace / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
                print("Mutation summary:", json.dumps(report["counts"], sort_keys=True))
                print("Report:", workspace / "summary.json")
                if code or not report["mutants"] or set(report["counts"]) != {"killed"}:
                    print("Review required: surviving mutants and runner errors are not passes.")
                    return 1
                return 0
            finally:
                shutil.rmtree(temporary)
        finally:
            # Only names generated by this invocation can reach these DROP statements.
            for name in ("test_" + database, database):
                conn.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
                )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, psycopg.Error, subprocess.TimeoutExpired):
        raise SystemExit("Mutation validation failed; sensitive diagnostics omitted.") from None
