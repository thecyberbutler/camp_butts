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
The web/provision/migration containers run as that identity. The proxy has no app secrets.
PostgreSQL's official entrypoint has only the initialization capabilities it needs, then
drops to postgres. Root initialization is not an application runtime role.

## Configuration and initialization

Copy `.env.example` to `.env`, fill the exact DNS hostname and dedicated UID/GID,
then generate a fresh `.secrets` directory as that identity. Do not reuse the test files
for production. Review subnet `172.30.10.0/28` for conflicts; if changed, update the
proxy address and `TRUSTED_PROXY_IPS` together. This setting must name only the proxy.

```sh
docker compose config --quiet
docker compose build
docker compose up -d db
docker compose run --rm provision
docker compose run --rm migrate migrate --noinput
docker compose run --rm migrate setup_roles
docker compose run --rm provision --grant-runtime
docker compose run --rm migrate collectstatic --noinput
docker compose up -d web proxy
docker compose exec web python manage.py check --deploy --fail-level WARNING
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
development proxy binds only loopback, uses Caddy's internal CA, and serves local assets.
Trust its root certificate on authorized test clients after checking its fingerprint;
for command-line validation pass `curl --cacert /protected/path/root.crt`. Never use
`--insecure` or disable browser certificate checks. Avoid installing trust globally
without an explicit operator choice. Django reload is enabled; security controls remain.

## Public domain and private network

Public domains use Caddy's supported automatic HTTPS and a trusted CA. For an isolated
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
