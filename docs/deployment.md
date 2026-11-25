# Deployment and host boundaries

Status: development. Do not expose this application to production until all release
gates are met. Compose is an implementation candidate, not a production approval.

## Host preparation

Use a supported patched Linux host with encrypted storage, synchronized time, a host
firewall, key-based SSH, restricted administration and no direct root SSH login. Expose
only 80/443 and explicitly approved private management access. Keep Docker management,
database, Gunicorn, backups and monitoring private. Docker access is host-root equivalent.

Create a dedicated non-root deployment identity (default UID/GID 10001). Secret files
must be owned by that identity and mode 0600; directory 0700. Compose file secrets on
local Docker are bind mounts: `uid`/`mode` declarations do not fix host ownership.
The web/provision/migration and database containers run as that identity. The proxy has no app secrets.
The custom PostgreSQL image owns its fresh data directory at build time, runs non-root
from entrypoint onward, and drops every Linux capability. No runtime root initialization
or privilege-drop helper is used. Required database authentication remains SCRAM.

## Configuration and initialization

Copy `.env.example` to `.env`, fill the exact DNS hostname and dedicated UID/GID,
then generate a fresh `.secrets` directory as that identity. Do not reuse the test files
for production. Review subnet `172.30.10.0/28` for conflicts; if changed, update the
proxy address and `TRUSTED_PROXY_IPS` together. This setting must name only the proxy.

```sh
docker compose config --quiet
docker compose build
docker compose up -d db
docker compose run --rm provision --create-campground pine-grove --name 'Pine Grove'
docker compose run --rm migrate tenant_command --campground pine-grove migrate --noinput
docker compose run --rm migrate tenant_command --campground pine-grove setup_roles
docker compose run --rm provision --grant-runtime --campground pine-grove --activate
docker compose run --rm migrate collectstatic --noinput
docker compose up -d web proxy
docker compose exec web python manage.py check --deploy --fail-level WARNING
docker compose exec -T web python - --campground pine-grove < scripts/check_database_boundary.py
```

Run one controlled migrator at a time. The provisioning service exists only in the
`tools` profile, has no public ports and is never kept running. It receives database
administration credentials only for initialization/grants. It does not silently rotate
existing passwords. Normal web startup does not migrate or receive migration/admin keys.
Reapply reviewed runtime grants after migrations; review new tables before granting.
Runtime can mutate necessary app tables but cannot migrate or update/delete audit history.

## Development

Use a separate Compose project, fresh secrets and database volumes. Set APP_DOMAIN and
DJANGO_ALLOWED_HOSTS to localhost. APP_UID can match the host file owner; choose a
dedicated GID unused by the base image (10001 is the default). Use:

```sh
docker compose -p campground-dev -f compose.yaml -f compose.dev.yaml up -d
```

Perform the initialization sequence above with the same project/overlay first. The
development proxy binds only loopback and loads a localhost-only development certificate.
Before first startup, generate its protected files with:

```sh
.venv/bin/python scripts/generate_dev_tls.py .secrets/dev-tls
```

The generator refuses overwrites and unprotected parent directories. It writes 0600
leaf-key/certificate files and a public CA certificate under a new 0700 directory. The
CA private key is discarded and never mounted. Verify the public CA fingerprint before
explicitly trusting it on authorized test clients. For command-line validation use
`curl --cacert .secrets/dev-tls/ca.crt https://localhost/`. Never use
`--insecure` or disable browser certificate checks. Avoid installing trust globally
without an explicit operator choice. Django reload is enabled; security controls remain.

## Public domain and private network

Public domains use Traefik ACME TLS-ALPN-01 automatic issuance/renewal and a trusted CA. For an isolated
private hostname use an explicitly configured internal CA and distribute trust securely.
The deployment has no published web/DB ports and no Docker socket mounts. Application
and DB networks are internal; the proxy alone has an edge network. Optional SMTP needs
an explicitly reviewed route to the approved SMTP host; this Compose configuration
deliberately does not supply unrestricted application egress. Never weaken verification
because SMTP, DNS or certificates fail.

## Release and updates

Take an encrypted backup; review dependency changes; run all checks and image scans;
rehearse restore and migrations on isolated copies. Verify actual TLS/CSRF/CSP behavior,
role permissions, mandatory MFA, authentication rate limits, log redaction, network
isolation and backup alerts. Set CPU/memory limits based on measured load. No coverage
percentage or scanner result replaces manual security review. Retain the previous
reviewed image for rollback; do not undo occupancy constraints or restore stale sessions.

## Database base-image changes

This implementation switched from Debian to patched Alpine images after security scans.
Never attach an existing Debian PostgreSQL physical data directory to the Alpine image:
libc/collation behavior and numeric ownership can differ. For existing installations,
use a verified encrypted logical dump, restore into a fresh isolated database volume,
rebuild indexes as required, revoke restored sessions, and validate before cutover.
Retain the previous volume and encrypted backup until recovery is proven. The local
validation used fresh volumes and preserved the old scratch volumes.

The database image upgrades libxml2 from the pinned base using the authenticated Alpine
repository. Record the resulting image digest and scanner report per build. Rebuild with
fresh package indexes for updates; an old successful build is not an ongoing security gate.

## Traefik migration and certificates

The owner approved this proxy substitution on 2026-11-24. Build the new proxy/web images,
run `collectstatic`, then recreate web/proxy with the same project name. No database
migration is introduced by this change. Do not delete the old Caddy volumes during the
change: they contain private certificate/CA material. They are no longer mounted. After
reviewed retention/recovery requirements are met, dispose of them through a separate
explicit operator action. Never dump or copy their private keys into logs or the repository.

Only the file provider is configured. Docker discovery/socket access, dashboard/API,
plugins, access logs, debug logs, version checks and anonymous telemetry are disabled.
Exact host validation prevents router-template injection. The proxy rejects unknown TLS
SNI, bounds requests to 65536 bytes and overwrites untrusted forwarding headers. It has
no application secrets or database network. Only the proxy publishes ports 80/443.

Production ACME requires the real public hostname, DNS and inbound TCP 443. Its private
account/certificate state lives in `traefik_data` (directory 0700, `acme.json` 0600).
The proxy starts as non-root and refuses insecure state permissions. No static fallback
certificate is supplied in production; issuance failure must not result in trusted HTTPS.
Public issuance/renewal and expiry alerting have not been exercised against a real domain;
validate them before release. Private domains require a reviewed internal-CA configuration;
the provided development overlay is intentionally limited to localhost.

Development certificates expire after 30 days. Generate a fresh protected directory,
verify and explicitly trust its new public CA, then switch the secret mounts and recreate
the proxy. Do not overwrite live-mounted private keys or disable validation. The development
CA is never a production trust anchor. No system-wide CA trust is installed automatically.

WhiteNoise serves only the collected static volume, read-only in web. Run collectstatic
and restart web after changing assets, including development; autorefresh/finders are
intentionally off. No uploads, secret directories or source files are mapped to static.

For an isolated stack on ports 80/443:

```sh
.venv/bin/python scripts/check_proxy_boundary.py --ca-file .secrets/dev-tls/ca.crt --campground pine-grove
```

For the scratch validation overlay used during development, add `--https-port 18443
--http-port 18080`. The check uses certificate validation and tests HTTP redirect,
security headers, static assets/traversal, header spoofing, unknown host/SNI, body size,
CSRF and absence of the Traefik API. Full PostgreSQL tests now also require the locally
built `campground-proxy:local` image for isolated negative startup checks.


## Campground provisioning and upgrades

Repeat register → tenant-scoped migrations → setup_roles → grants/activation for every
campground, using a new lowercase hyphenated slug and display name. Registration generates
an immutable UUID/schema binding and leaves the tenant inactive. Migrations create separate
accounts, MFA, permissions, sessions, caches, inventory and audit tables. Activation applies
FORCE RLS and the restrictive UUID guard to every tenant table, then grants runtime access
and records the operator event. Incomplete migrations prevent grants/activation. New tenants
receive the directory name as initial branding; adopted/custom branding is retained.

The directory is exposed at `/`; `/?campground=pine-grove` redirects to `/c/pine-grove/`.
Directory display names/slugs are public. No web endpoint may mutate directory state.
Schema identifiers are derived from registered UUIDs, never URL text. Staff administration
is independent per campground; there is no platform superuser web interface.

To adopt the existing single-campground database, first rehearse with an encrypted isolated
copy. Stop web/proxy and scheduled jobs during cutover. Preserve the original volume and
backup. With the new image run:

```sh
docker compose run --rm provision --create-campground pine-grove --name 'Pine Grove' --adopt-existing
docker compose run --rm migrate tenant_command --campground pine-grove migrate --noinput
docker compose run --rm migrate tenant_command --campground pine-grove setup_roles
docker compose run --rm provision --grant-runtime --campground pine-grove --activate
docker compose run --rm migrate collectstatic --noinput
docker compose up -d web proxy
```

Adoption preserves tables/data/constraints in public, moves btree_gist objects into the
controlled extension schema and protects the existing tables in the same operator transaction.
Only one directory entry can own public. New tenants never search public. Adoption is a
one-time explicit operation, not an idempotent command to repeat on an already registered slug.
All users must sign in again; resend pending confirmation/recovery links through the usual
controlled flows. Old unprefixed application links fail closed. Secrets remain unchanged and
are never printed or copied into directory records.

For upgrades, stop affected routing/jobs, run migrations for each explicitly selected slug,
then reapply its runtime grants before activation. New Django migrations still live alongside
the domain apps; each schema maintains its own django_migrations table. Tenant directory/RLS
DDL lives in the operator provisioning helper, not an ordinary runtime migration. The command
wrapper uses an atomic scope; migrations requiring nontransactional DDL need a separately
reviewed execution design and must not be forced through by disabling security controls.
The default `migrate` Compose service refuses to operate without explicit command/tenant args.

Run `check --deploy` and `collectstatic` globally because they do not select campground data.
Run migration consistency checks and domain commands with `tenant_command --campground SLUG`.
Check cross-schema isolation in both directions using two active synthetic tenants:

```sh
docker compose exec -T web python - --campground pine-grove --other-campground lake-view < scripts/check_database_boundary.py
docker compose exec -T web python - --campground lake-view --other-campground pine-grove < scripts/check_database_boundary.py
docker compose run --rm migrate tenant_command --campground pine-grove makemigrations --check --dry-run
```

Global directory/operator events need an encrypted platform recovery procedure in addition
to the tenant backups described in backup-and-restore.md. Full multi-tenant restore validation
is still a release blocker. No production data was adopted or deployed during development.
