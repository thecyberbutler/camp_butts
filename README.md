# Campground reservations

A self-hosted Django application for approximately 100 campers. **Development version:
not production-ready.** See [implementation progress](docs/implementation-progress.md)
for verified functionality and outstanding release gates.

Implemented: approval-first registration, optional invitation/open/disabled modes,
allauth password/TOTP authentication, encrypted sessions/MFA storage, camper search,
transactional reservations and maintenance blocks, modification/cancellation, local
notifications, controlled SVG availability map, staff operations/calendar and limited CSV
exports. PostgreSQL exclusion constraints are authoritative for occupancy. No payments,
external authentication, CDN assets or managed services.

## Stack and organization

Python 3.13; Django 5.2 LTS; Poetry; Psycopg 3; PostgreSQL 17; allauth; Axes;
Argon2id; Gunicorn; Caddy; Django templates; local Bootstrap 5 and HTMX.
`apps/` contains domain modules; `config/` holds security settings; services own
reservation policies and transactions. Read AGENTS.md and PROJECT_SPEC.md before changes.

## Local installation and tests

Install Python 3.13, Poetry 2.5.2 and Docker Compose. Use a dedicated checkout and
synthetic data. Never copy production secrets or data into development.

```sh
POETRY_VIRTUALENVS_IN_PROJECT=true poetry sync
python3.13 scripts/generate_secrets.py .secrets
```

The generator writes mode-0600 files in a mode-0700 directory and refuses overwrites.
It never displays credentials. `.gitignore` and the Docker context exclude secret material.
If TLS validation fails, configure the correct trusted CA bundle; never turn verification off.

For the isolated PostgreSQL suite:

```sh
docker run -d --name campground-test-db \
  -p 127.0.0.1:55432:5432 \
  --mount type=bind,src="$PWD/.secrets/admin_password",dst=/run/secrets/admin_password,readonly \
  -e POSTGRES_PASSWORD_FILE=/run/secrets/admin_password \
  -e POSTGRES_DB=campground_test \
  -e POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 \
  --security-opt no-new-privileges:true --memory 512m --cpus 2 \
  postgres:17.12-bookworm@sha256:1eff563f6c868b9b433566e9f3cf6e5c79fbd3b95bf70ec7277d376cdbfc50d7
.venv/bin/python scripts/provision_test_db.py
sh scripts/test.sh -q --cov --cov-report=term-missing
```

The test runner is a non-superuser with CREATEDB only for disposable test databases.
Runtime production permissions are separate and do not include CREATEDB. Tests retain
HTTPS, CSRF, Argon2id, Axes and MFA. They never substitute SQLite.

## Local application and deployment

Follow [deployment](docs/deployment.md) for initialization and the loopback-only
development overlay. Development still uses HTTPS with a properly trusted local CA;
DEBUG is false. Production has no public PostgreSQL/Gunicorn ports.

Configuration is explicit in `.env.example`; only non-secret values and file paths
belong in `.env`. SMTP defaults off. In-app notifications work without SMTP; recovery
and email changes do not pretend to work. See [administration](docs/administration.md)
for the first administrator, approval, MFA, policy setup and scheduled commands.

## Validation

```sh
poetry check --lock
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/pip-audit --progress-spinner off
sh scripts/test.sh -q --cov --cov-fail-under=85
docker compose config --quiet
docker compose build
docker compose exec web python manage.py check --deploy --fail-level WARNING
docker compose run --rm migrate makemigrations --check --dry-run
```

`scripts/security-check.sh` adds Gitleaks and Trivy when those tools are installed.
Scan tracked source and complete Git history before release; this initial directory
did not contain Git metadata. Scan all three deployment images, including OS packages.
No source is sent to external scanning services. Package audits query package/version
advisories; scanners download advisory databases.

See [backup and restore](docs/backup-and-restore.md), [security](docs/security.md),
[threat model](docs/threat-model.md), [decisions](docs/security-decisions.md),
[incident response](docs/incident-response.md), and [dependencies](docs/dependency-inventory.md).
On errors, check protected file ownership, explicit hosts, service health and audit events.
Never enable DEBUG, dump settings/requests, remove constraints or bypass MFA to troubleshoot.
