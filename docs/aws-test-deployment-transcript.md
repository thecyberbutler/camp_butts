# AWS test deployment: exact execution transcript

Prepared 2026-11-24 before remote changes. The read-only preflight was disclosed and
executed separately. These commands target only the owner-authorized test instance.
They contain no secret values. Do not enable shell tracing or print generated secret files.
No login account is created for application users. This script refuses an existing install;
a failure needs a separately disclosed recovery transcript, not a blind rerun.

## Local commands (in this repository)

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'umask 077; mkdir -m 700 /home/ec2-user/camp-butts-test-deploy'

scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/compose.yaml /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/compose.registry.yaml /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/generate_secrets.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/check_database_boundary.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/deploy_aws_test.sh /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-deploy-935cbb3b3a29/bundle.sha256 camp-butts-test:/home/ec2-user/camp-butts-test-deploy/

ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash /home/ec2-user/camp-butts-test-deploy/deploy_aws_test.sh'

SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
```

## Uploaded deployment script executed with sudo

```bash
#!/usr/bin/env bash
# Fresh Amazon Linux 2023 test host only. Review this entire script before SSH.
set -euo pipefail
umask 077
stage=preconditions
trap 'printf "Deployment stopped during %s; no raw diagnostics displayed.\n" "$stage" >&2' ERR
test "$(id -u)" = 0
test "$(uname -m)" = x86_64
test "$(. /etc/os-release; printf '%s' "$ID:$VERSION_ID")" = amzn:2023
test ! -e /opt/camp-butts-test
! getent passwd 10001 >/dev/null
! getent group 10001 >/dev/null
! getent passwd campground-test >/dev/null
! getent group campground-test >/dev/null
cd /home/ec2-user/camp-butts-test-deploy
sha256sum --check bundle.sha256

stage=installing-docker
# Use the configured Amazon signed repositories; do not add Docker-group members.
dnf install --releasever=latest -y docker python3 >/dev/null 2>&1
systemctl enable --now docker >/dev/null 2>&1

stage=installing-verified-compose
install -d -m 0755 /usr/local/lib/docker/cli-plugins
test ! -e /usr/local/lib/docker/cli-plugins/docker-compose
python3 - <<'PY'
import hashlib
import os
import urllib.request

url = "https://github.com/docker/compose/releases/download/v5.8.0/docker-compose-linux-x86_64"
expected = "b8840f5008c447f41fce0a57ae3adeab42c89b1eb6e6012524bcabbfb4ffbaf6"
try:
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(150 * 1024 * 1024 + 1)
    if len(data) > 150 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Digest mismatch")
    path = "/usr/local/lib/docker/cli-plugins/docker-compose"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o755)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
    os.chmod(path, 0o755)
except Exception:
    raise SystemExit("Compose installation refused; diagnostics withheld.") from None
PY
docker version --format '{{.Server.Version}}'
docker compose version

stage=checking-network-boundaries
test -z "$(docker ps -aq --filter label=com.docker.compose.project=camp-butts-test)"
test -z "$(docker volume ls -q --filter label=com.docker.compose.project=camp-butts-test)"
test "$(ss -Hltn '( sport = :80 or sport = :443 )' | wc -l)" -eq 0
# Refuse conflicting host routes or existing Docker networks, rather than changing them.
ip -j route show > routes.json
docker network inspect $(docker network ls -q) > networks.json
python3 - <<'PY'
import ipaddress
import json

target = ipaddress.ip_network("172.30.10.0/28")
routes = [r.get("dst", "default") for r in json.load(open("routes.json"))]
subnets = [c.get("Subnet", "") for n in json.load(open("networks.json"))
           for c in n.get("IPAM", {}).get("Config") or []]
for value in routes + subnets:
    if value in ("default", "", "0.0.0.0/0", "::/0"):
        continue
    network = ipaddress.ip_network(value, strict=False)
    if network.version == 4 and target.overlaps(network):
        raise SystemExit("Deployment subnet conflicts with an existing network.")
PY

stage=creating-protected-deployment
groupadd --gid 10001 campground-test
useradd --uid 10001 --gid 10001 --no-create-home --home-dir /nonexistent --shell /sbin/nologin campground-test
install -d -m 0750 -o root -g campground-test /opt/camp-butts-test
install -m 0640 -o root -g campground-test compose.yaml compose.registry.yaml images.env generate_secrets.py check_database_boundary.py /opt/camp-butts-test/
install -d -m 0700 -o campground-test -g campground-test /opt/camp-butts-test/.secrets
cat > /opt/camp-butts-test/.env <<'EOF'
APP_DOMAIN=camp-butts-test.thecyberbutler.io
DJANGO_ALLOWED_HOSTS=camp-butts-test.thecyberbutler.io
APP_ENVIRONMENT=development
APP_UID=10001
APP_GID=10001
APP_TIME_ZONE=America/New_York
SECRETS_DIR=/opt/camp-butts-test/.secrets
EOF
chmod 0600 /opt/camp-butts-test/.env
sudo -u campground-test python3 /opt/camp-butts-test/generate_secrets.py /opt/camp-butts-test/.secrets
cd /opt/camp-butts-test
dc() {
  docker compose -p camp-butts-test --env-file .env --env-file images.env -f compose.yaml -f compose.registry.yaml "$@"
}

stage=pulling-digest-locked-images
dc config --quiet
dc --profile tools pull >/dev/null 2>&1
stage=initializing-database
dc up -d --no-build --wait --wait-timeout 120 db >/dev/null 2>&1
dc run --rm provision --create-campground georgia-mountain-fairgrounds --name 'Georgia Mountain Fairgrounds' >/dev/null 2>&1
stage=migrating-campground
dc run --rm migrate tenant_command --campground georgia-mountain-fairgrounds migrate --noinput >/dev/null 2>&1
dc run --rm migrate tenant_command --campground georgia-mountain-fairgrounds setup_roles >/dev/null 2>&1
stage=importing-inactive-drafts
dc run --rm migrate tenant_command --campground georgia-mountain-fairgrounds import_campground --file /app/data/campgrounds/georgia-mountain-fairgrounds.json >/dev/null 2>&1
stage=protecting-and-activating-profile
dc run --rm provision --grant-runtime --campground georgia-mountain-fairgrounds --activate >/dev/null 2>&1
stage=collecting-static-assets
dc run --rm migrate collectstatic --noinput >/dev/null 2>&1
stage=starting-https-application
dc up -d --no-build --wait --wait-timeout 180 web proxy >/dev/null 2>&1
stage=validating-deployment
dc exec -T web python manage.py check --deploy --fail-level WARNING >/dev/null 2>&1
dc exec -T web python - --campground georgia-mountain-fairgrounds < check_database_boundary.py
dc ps --format '{{.Service}} {{.State}} {{.Health}} {{.Publishers}}'
printf '%s\n' 'Deployment initialized. External certificate/banner/security checks remain required.'
```

## Immutable image references

```dotenv
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:403cb21fa55d8a3968bdf55480506e1552b4de46c9d137e0ad1b3e824dd07845
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:1462cd37db5951265dc8a6f071a69e059151037454b31c6d866970cdd0a57a05
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:c2258e9c88972ed99c604104d792be12d7753e6000d47410136596cc4314f578
```

## Uploaded file checksums

```text
bbb2c6251ebe658514638b7d1ac6c3f11d763a19a4fab52fc237e8c306b50dde  check_database_boundary.py
e9ff9a5ba3bde237d5631ebed1cae33da2fed467a1e0e449681199be139571e0  compose.registry.yaml
292f300e9b510be358693aebd2b6e839426b047b70b2b216aa4c7670467c880a  compose.yaml
f0ac0e4d6963bd8876473f6dc7de79d3bdcb7e82c7662e18c17fac37bcce6049  deploy_aws_test.sh
7ad8e56f664b691096614dccc2f89b19bce6cdc66fa5f786d6f8aa7b9f64decf  generate_secrets.py
8ca6ada65b4eaf38ab8da8ae2dd1b82af968f5ceeb8a26c0c356f8d8c6cd9edc  images.env
```

## Supporting files

### compose.yaml

```yaml
name: campground
x-app: &app
  build:
    context: .
    args:
      APP_UID: ${APP_UID:-10001}
      APP_GID: ${APP_GID:-10001}
  image: campground-web:local
  user: "${APP_UID:-10001}:${APP_GID:-10001}"
  read_only: true
  cap_drop: [ALL]
  security_opt: [no-new-privileges:true]
  tmpfs:
    - /tmp:rw,noexec,nosuid,size=32m,mode=1777
    - /run/gunicorn:rw,noexec,nosuid,size=16m,mode=0700,uid=${APP_UID:-10001},gid=${APP_GID:-10001}
  pids_limit: 128
  mem_limit: 1g
  cpus: 2
  environment: &environment
    DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:?Set explicit allowed hosts}
    APP_TIME_ZONE: ${APP_TIME_ZONE:-America/New_York}
    APP_ENVIRONMENT: ${APP_ENVIRONMENT:-production}
    DJANGO_SECRET_KEY_FILE: /run/secrets/django_key
    MFA_KEY_FILE: /run/secrets/mfa_key
    SESSION_KEY_FILE: /run/secrets/session_key
    DATABASE_PASSWORD_FILE: /run/secrets/database_password
    DATABASE_NAME: campground
    DATABASE_USER: campground_app
    DATABASE_HOST: db
    TRUSTED_PROXY_IPS: 172.30.10.2
    EMAIL_ENABLED: "false"
  secrets: [django_key, mfa_key, session_key, database_password]

services:
  provision:
    image: campground-web:local
    profiles: [tools]
    user: "${APP_UID:-10001}:${APP_GID:-10001}"
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    networks: [database]
    secrets: [admin_password, migration_password, database_password]
    entrypoint: [python, /app/scripts/provision_database.py]
    restart: "no"
  web:
    <<: *app
    restart: unless-stopped
    networks:
      application:
        ipv4_address: 172.30.10.3
      database: {}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: [CMD, python, manage.py, check, --deploy, --fail-level, WARNING]
      interval: 60s
      timeout: 15s
      retries: 3
    volumes:
      - static:/app/staticfiles:ro
  migrate:
    <<: *app
    profiles: [tools]
    restart: "no"
    networks: [database]
    entrypoint: [python, manage.py]
    command: [tenant_command]
    environment:
      <<: *environment
      DJANGO_SETTINGS_MODULE: config.settings.migration
      DATABASE_USER: campground_migrator
      DATABASE_PASSWORD_FILE: /run/secrets/migration_password
    secrets: [django_key, mfa_key, session_key, migration_password]
    volumes:
      - static:/app/staticfiles
  db:
    build:
      context: .
      dockerfile: Dockerfile.db
      args:
        APP_UID: ${APP_UID:-10001}
        APP_GID: ${APP_GID:-10001}
    image: campground-db:local
    user: "${APP_UID:-10001}:${APP_GID:-10001}"
    restart: unless-stopped
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=32m
      - /var/run/postgresql:rw,noexec,nosuid,size=16m,mode=0700,uid=${APP_UID:-10001},gid=${APP_GID:-10001}
    pids_limit: 128
    mem_limit: 1g
    cpus: 2
    networks: [database]
    environment:
      POSTGRES_DB: campground
      POSTGRES_PASSWORD_FILE: /run/secrets/admin_password
      POSTGRES_INITDB_ARGS: --auth-host=scram-sha-256 --auth-local=scram-sha-256
    secrets: [admin_password]
    volumes:
      - postgres:/var/lib/postgresql/data
    command: [postgres, -c, password_encryption=scram-sha-256, -c, log_statement=none, -c, log_min_error_statement=panic, -c, log_error_verbosity=terse]
    healthcheck:
      test: [CMD, pg_isready, -U, postgres, -d, campground]
      interval: 10s
      timeout: 5s
      retries: 5
  proxy:
    build:
      context: .
      dockerfile: Dockerfile.proxy
      args:
        APP_UID: ${APP_UID:-10001}
        APP_GID: ${APP_GID:-10001}
    image: campground-proxy:local
    restart: unless-stopped
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    tmpfs: ["/tmp:rw,noexec,nosuid,size=16m"]
    pids_limit: 128
    mem_limit: 256m
    cpus: 1
    ports: ["80:8080", "443:8443"]
    environment:
      APP_DOMAIN: ${APP_DOMAIN:?Set the HTTPS hostname}
      TLS_MODE: acme
      HTTPS_PORT: "443"
    networks:
      edge: {}
      application:
        ipv4_address: 172.30.10.2
    volumes:
      - traefik_data:/data
    depends_on: [web]

networks:
  edge: {}
  application:
    internal: true
    ipam:
      config:
        - subnet: 172.30.10.0/28
  database:
    internal: true

volumes:
  postgres: {}
  static: {}
  traefik_data: {}

secrets:
  django_key:
    file: ${SECRETS_DIR:-./.secrets}/django_key
  mfa_key:
    file: ${SECRETS_DIR:-./.secrets}/mfa_key
  session_key:
    file: ${SECRETS_DIR:-./.secrets}/session_key
  database_password:
    file: ${SECRETS_DIR:-./.secrets}/database_password
  migration_password:
    file: ${SECRETS_DIR:-./.secrets}/migration_password
  admin_password:
    file: ${SECRETS_DIR:-./.secrets}/admin_password
```

### compose.registry.yaml

```yaml
# Use with compose.yaml and a generated release images.env. No local builds.
services:
  web:
    build: !reset null
    image: ${CAMPGROUND_WEB_IMAGE:?Set the verified web image digest}
    pull_policy: missing
  migrate:
    build: !reset null
    image: ${CAMPGROUND_WEB_IMAGE:?Set the verified web image digest}
    pull_policy: missing
  provision:
    image: ${CAMPGROUND_WEB_IMAGE:?Set the verified web image digest}
    pull_policy: missing
  db:
    build: !reset null
    image: ${CAMPGROUND_DB_IMAGE:?Set the verified database image digest}
    pull_policy: missing
  proxy:
    build: !reset null
    image: ${CAMPGROUND_PROXY_IMAGE:?Set the verified proxy image digest}
    pull_policy: missing
```

### generate_secrets.py

```python
"""Create fresh secret files without ever printing secret material."""

import argparse
import os
import secrets
from pathlib import Path


def generate(directory: Path) -> None:
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_mode & 0o077:
        raise SystemExit("Secret directory must be private (0700), not a symlink.")
    # 32 random bytes in urlsafe base64 is a Fernet key; no custom cryptography.
    import base64

    values = {
        "django_key": secrets.token_urlsafe(64),
        "mfa_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "session_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "database_password": secrets.token_urlsafe(48),
        "migration_password": secrets.token_urlsafe(48),
        "admin_password": secrets.token_urlsafe(48),
    }
    if any((directory / name).exists() for name in values):
        raise SystemExit("Refusing to overwrite existing secrets.")
    for name, value in values.items():
        fd = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(value)
    print("Created protected secret files; values are not displayed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    generate(parser.parse_args().directory)
```

### check_database_boundary.py

```python
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
```

## External HTTPS validation code

```python
"""Verify the public test deployment without printing cookies, headers or response bodies."""

import http.client
import socket
import ssl
import sys

HOST = "camp-butts-test.thecyberbutler.io"
PREFIX = "/c/georgia-mountain-fairgrounds"
BANNER = b"THIS IS A TEST INSTANCE"


class ValidationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def check():
    context = ssl.create_default_context()

    def request(path, *, method="GET", headers=None, body=None):
        connection = http.client.HTTPSConnection(HOST, context=context, timeout=15)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            data = response.read(2 * 1024 * 1024 + 1)
            require(len(data) <= 2 * 1024 * 1024, "Unexpected response size")
            return response.status, {k.lower(): v for k, v in response.getheaders()}, data
        finally:
            connection.close()

    for path, expected in (
        ("/", 200),
        (PREFIX + "/", 200),
        (PREFIX + "/accounts/login/", 200),
        (PREFIX + "/accounts/signup/", 200),
        (PREFIX + "/campsites/", 200),
        (PREFIX + "/missing/", 404),
    ):
        status, headers, data = request(path)
        require(status == expected, "Unexpected page status")
        require(data.count(BANNER) == 1, "Missing or duplicate test banner")
        require(headers.get("x-content-type-options") == "nosniff", "Missing nosniff")
        require("max-age=31536000" in headers.get("strict-transport-security", ""), "Missing HSTS")
        require("default-src 'none'" in headers.get("content-security-policy", ""), "Missing CSP")
        require("no-store" in headers.get("cache-control", ""), "Missing private cache policy")
    for path in (
        "/static/vendor/bootstrap.min.css",
        "/static/vendor/htmx.min.js",
        "/static/css/app.css",
    ):
        status, _, data = request(path)
        require(status == 200, "Missing local static asset")
        if path.endswith("app.css"):
            require(
                b".test-instance-banner" in data and b"#b91c1c" in data, "Missing red banner CSS"
            )
    status, _, _ = request("/", headers={"Host": "untrusted.invalid"})
    require(status in (404, 421), "Unknown host routed to application")
    status, _, _ = request(
        "/",
        headers={"X-Forwarded-Proto": "http", "X-Real-IP": "invalid", "Forwarded": "proto=http"},
    )
    require(status == 200, "Forwarding-header boundary failed")
    status, _, data = request(PREFIX + "/accounts/login/", method="POST", body=b"login=synthetic")
    require(status == 403 and BANNER in data, "CSRF or error banner check failed")
    status, _, _ = request(PREFIX + "/accounts/login/", method="POST", body=b"x" * 65537)
    require(status == 413, "Request body limit not enforced")
    for path in ("/api/rawdata", "/dashboard/", "/static/%2e%2e/.secrets/django_key"):
        status, _, _ = request(path)
        require(status != 200, "Unexpected private resource exposure")
    plain = http.client.HTTPConnection(HOST, timeout=15)
    try:
        plain.request("GET", "/")
        response = plain.getresponse()
        require(response.status in (301, 308), "HTTP did not redirect")
        require(response.getheader("Location") == f"https://{HOST}/", "Unexpected redirect target")
        response.read()
    finally:
        plain.close()
    with socket.create_connection((HOST, 443), timeout=15) as sock:
        try:
            with context.wrap_socket(sock, server_hostname="untrusted.invalid"):
                raise ValidationError("Unknown SNI accepted")
        except ssl.SSLCertVerificationError:
            raise ValidationError("Unknown SNI received a fallback certificate") from None
        except ssl.SSLError:
            pass
    print(
        "Public HTTPS, banner, static assets, security headers, CSRF, "
        "host/SNI and body limits verified."
    )


if __name__ == "__main__":
    try:
        check()
    except Exception as error:
        message = (
            str(error) if isinstance(error, ValidationError) else "Transport/configuration failure"
        )
        print(f"Public test validation failed: {message}", file=sys.stderr)
        raise SystemExit(1) from None
```

## Follow-up: read-only runtime verification

Disclosed before execution. Reads secret metadata only, never file contents.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' < /Users/michaelbutler/Repos/camp_butts/.runtime/aws-test-verify.sh
```

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /opt/camp-butts-test
dc() {
  docker compose -p camp-butts-test --env-file .env --env-file images.env -f compose.yaml -f compose.registry.yaml "$@"
}
rpm -q docker python3
for service in web db proxy; do
  printf '%s\n' "$service"
  docker inspect --format '{{.Config.User}} readonly={{.HostConfig.ReadonlyRootfs}} caps={{json .HostConfig.CapDrop}} security={{json .HostConfig.SecurityOpt}} ports={{json .NetworkSettings.Ports}}' "$(dc ps -q "$service")"
done
python3 - <<'CHECK_PERMISSIONS'
from pathlib import Path
p = Path(".secrets")
assert not p.is_symlink() and p.stat().st_mode & 0o777 == 0o700
for n in ("django_key", "mfa_key", "session_key", "database_password", "migration_password", "admin_password"):
    f = p / n
    s = f.lstat()
    assert not f.is_symlink() and f.is_file() and s.st_mode & 0o777 == 0o600
    assert s.st_uid == 10001 and s.st_gid == 10001
print("Secret ownership and permissions verified; values were not read.")
CHECK_PERMISSIONS
dc exec -T web python - <<'CHECK_APP'
import django
django.setup()
from django.conf import settings
from apps.tenancy.context import lookup, tenant_scope
from apps.configuration.models import Campground
from apps.campsites.models import Campsite
from django.contrib.auth import get_user_model
try:
    assert settings.APP_ENVIRONMENT == "development"
    assert not settings.DEBUG and settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        profile = Campground.current()
        assert not profile.booking_enabled and not profile.public_availability
        assert Campsite.objects.count() == 216 and not Campsite.objects.filter(active=True).exists()
        assert get_user_model().objects.count() == 0
    print("Development banner, secure settings, 216 inactive drafts, closed booking and zero accounts verified.")
except Exception:
    raise SystemExit("Application state validation failed; diagnostics withheld.") from None
CHECK_APP
```

## Follow-up: read-only progress inspection

Disclosed before execution while startup was in progress:

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n docker ps -a --filter label=com.docker.compose.project=camp-butts-test --format "{{.Names}} {{.Status}}"; sudo -n docker image ls --format "{{.Repository}} {{.Tag}}"'
```

Execution completed successfully. The progress query ran before the final read-only audit;
the HTTPS check was started during startup and completed successfully. No recovery commands,
security exceptions, log dumps, firewall changes, or additional remote mutations were used.
