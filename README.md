# Campground reservations

A self-hosted Django SaaS application for multiple campgrounds, initially approximately
100 campers per campground. **Development version:
not production-ready.** See [implementation progress](docs/implementation-progress.md)
for verified functionality and outstanding release gates.

Implemented: approval-first registration, optional invitation/open/disabled modes,
allauth password/TOTP authentication, encrypted sessions/MFA storage, camper search,
transactional reservations and maintenance blocks, modification/cancellation, local
notifications, controlled SVG availability map, staff operations/calendar and limited CSV
exports, camper deactivation/reactivation, campsite classification management and an
audited read-only audit viewer. PostgreSQL exclusion constraints are authoritative for occupancy. Optional [Google sign-in](docs/google-oauth.md) uses the owner-approved restricted egress
exception; local authentication remains available. No payments, CDN assets or managed
database services.

## Multiple campgrounds

Open `/?campground=pine-grove` to select a registered campground; the application redirects
to `/c/pine-grove/`. The root directory lists active campgrounds. Accounts are separate:
the same email/username can belong to different campground accounts. Campground staff
permissions never grant platform provisioning rights. The first implementation supports
one active campground login per browser cookie jar; sign in again when switching.

The existing stack remains suitable. Shared application/database infrastructure contains
separate PostgreSQL schemas, with forced row security and tenant-bound sessions and
confirmation/recovery tokens. See [architecture assessment](docs/saas-architecture.md).
Upgrading invalidates existing sessions and pending confirmation/reset links. Provision
and activate tenants using the explicit steps in [deployment](docs/deployment.md).

## Stack and organization

Python 3.13; Django 5.2 LTS; Poetry; Psycopg 3; PostgreSQL 17; allauth; Axes;
Argon2id; Gunicorn; Traefik; WhiteNoise; Django templates; local Bootstrap 5 and HTMX.
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

For the isolated PostgreSQL suite (build `campground-proxy:local` with `docker compose build proxy`
first; container boundary tests require it):

```sh
# Match the protected secret-file owner; select a dedicated unused group ID.
TEST_UID="$(id -u)"
TEST_GID=10001
docker build -f Dockerfile.db --build-arg APP_UID="$TEST_UID" \
  --build-arg APP_GID="$TEST_GID" -t campground-test-postgres:local .
docker run -d --name campground-test-db \
  --user "$TEST_UID:$TEST_GID" --read-only --cap-drop ALL \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --tmpfs /var/run/postgresql:rw,noexec,nosuid,size=16m,mode=0700,uid="$TEST_UID",gid="$TEST_GID" \
  -p 127.0.0.1:55432:5432 \
  --mount type=bind,src="$PWD/.secrets/admin_password",dst=/run/secrets/admin_password,readonly \
  -e POSTGRES_PASSWORD_FILE=/run/secrets/admin_password \
  -e POSTGRES_DB=campground_test \
  -e 'POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 --auth-local=scram-sha-256' \
  --security-opt no-new-privileges:true --memory 512m --cpus 2 \
  campground-test-postgres:local postgres -c log_statement=none \
  -c log_min_error_statement=panic -c log_error_verbosity=terse
# Wait for pg_isready before provisioning; never disable authentication.
docker exec campground-test-db pg_isready -U postgres -d campground_test
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
docker compose run --rm migrate tenant_command --campground pine-grove makemigrations --check --dry-run
```

`scripts/security-check.sh` adds Gitleaks and Trivy when those tools are installed.
Scan tracked source and complete Git history before release. Git is now initialized and
the current history scan passed. Scan all deployment images, including OS packages and the optional Google egress image.
The current application/database and replacement Traefik image HIGH/CRITICAL gates passed.
Historical Caddy findings are retained with their removal disposition.
See [security findings](docs/security-findings.md).
Use `TEST_DATABASE_PORT=55433` with provisioning and `scripts/test.sh` when using the
existing hardened test container from this development session. Do not reuse production
volumes for test initialization.

No source is sent to external scanning services. Package audits query package/version
advisories; scanners download advisory databases.

See [backup and restore](docs/backup-and-restore.md), [security](docs/security.md),
[threat model](docs/threat-model.md), [decisions](docs/security-decisions.md),
[incident response](docs/incident-response.md), and [dependencies](docs/dependency-inventory.md).
On errors, check protected file ownership, explicit hosts, service health and audit events.
Never enable DEBUG, dump settings/requests, remove constraints or bypass MFA to troubleshoot.

## Georgia Mountain Fairgrounds and mutation testing

The first real campground profile is `georgia-mountain-fairgrounds`; choose it through
`/?campground=georgia-mountain-fairgrounds`. Its 216 map-derived sites are **inactive drafts**,
not verified inventory. Online booking is closed pending roster/rate/policy reconciliation.
See [source review and operator import](docs/georgia-mountain-fairgrounds.md).

Mutmut 3.8.1 is development-only. After the protected PostgreSQL test setup:

```sh
.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
```

Read [mutation isolation, reports and limitations](docs/mutation-testing.md) before expanding
the campaign. Never apply mutants to application source or run them against production.
Current validation and remaining release gates are in `docs/implementation-progress.md`.

## Prebuilt Docker Hub images

The owner-approved public repositories are `thecyberbutler/campground-web`,
`thecyberbutler/campground-db` and `thecyberbutler/campground-proxy`, with AMD64/ARM64
prereleases. Use [the publishing/deployment guide](docs/container-publishing.md) and the
verified `releases/<tag>/images.env` with `compose.registry.yaml` to deploy without local
builds. Published images use UID/GID 10001; keep secrets 0600 and owned by that deployment
identity. All existing migration, HTTPS and release requirements remain. No stable/latest
release or production-readiness claim is made.

Public development instances can use `APP_ENVIRONMENT=development` with production settings
to display the red **THIS IS A TEST INSTANCE** banner while retaining all security controls.
`test` also displays it; `production` hides it; other values are rejected. See
[the AWS test deployment procedure](docs/deployment.md#aws-public-development-instance).

Google sign-in is deployed on the AWS test instance in prerelease
`0.1.0-alpha.20261125-3386d5caf5b3`. Automated public/runtime checks passed; real human
Google consent and approved-user login remain pending. See [Google setup](docs/google-oauth.md)
and the [executed upgrade transcript](docs/aws-google-deployment-transcript.md).

The shared interface uses rounded cards and forms, warm colors, subtle interactions and
responsive navigation with reduced-motion support. All styles and illustrations are local.
See [interface design](docs/interface-design.md) for behavior, accessibility checks and
deployment status. Completed features are recorded in separate validated Git commits.
