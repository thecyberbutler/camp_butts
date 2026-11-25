# Exact AWS Google upgrade transcript — 2026-11-25

Prepared before connecting. Target: existing owner-authorized AWS test deployment via
`ssh camp-butts-test`. This is an additive first-enable upgrade, not a fresh installation.
No credential values are included or transferred. The owner-installed Google file is read
only inside its intended runtime container for validation/use. Existing SSH host verification
is mandatory; no agent forwarding or connection sharing is enabled.

The commands below run sequentially only after the reviewed images have been published
and their remote digests verified. The upgrade briefly stops web writes, creates an encrypted
DB snapshot, applies vendor migrations/least-privilege grants, starts the optional restricted
proxy and new web image, then checks runtime controls. Failure stops execution and retains
volumes/secrets/recovery files. No destructive rollback is automatic.

## Exact local SSH/SCP commands

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'umask 077; mkdir /home/ec2-user/camp-butts-google-upgrade'
scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/baseline-images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/check_database_boundary.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/compose.google.yaml /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/compose.registry.yaml /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/compose.yaml /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/encrypt_deployment_snapshot.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/upgrade_aws_google.sh /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/verify_aws_google.sh /Users/michaelbutler/Repos/camp_butts/.runtime/aws-google-upgrade-3386d5caf5b3/bundle.sha256 camp-butts-test:/home/ec2-user/camp-butts-google-upgrade/
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash /home/ec2-user/camp-butts-google-upgrade/upgrade_aws_google.sh'
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash /home/ec2-user/camp-butts-google-upgrade/verify_aws_google.sh'
```

## Exact transferred files

### baseline-images.env

```text
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:403cb21fa55d8a3968bdf55480506e1552b4de46c9d137e0ad1b3e824dd07845
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:1462cd37db5951265dc8a6f071a69e059151037454b31c6d866970cdd0a57a05
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:c2258e9c88972ed99c604104d792be12d7753e6000d47410136596cc4314f578
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
        "SELECT 1 FROM socialaccount_socialapp LIMIT 0",
        "UPDATE socialaccount_socialtoken SET token=token WHERE false",
        "INSERT INTO socialaccount_socialtoken (token) SELECT '' WHERE false",
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
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM socialaccount_socialtoken LIMIT 0")
        cursor.execute("DELETE FROM socialaccount_socialtoken WHERE false")
        cursor.execute(
            "SELECT count(*) FROM pg_class WHERE relnamespace=current_schema()::regnamespace "
            "AND relname IN ('socialaccount_socialaccount', 'socialaccount_socialtoken', "
            "'socialaccount_socialapp') AND relrowsecurity AND relforcerowsecurity"
        )
        if cursor.fetchone()[0] != 3:
            raise RuntimeError("Social account tables lack forced tenant isolation")
        transaction.set_rollback(True)
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

### compose.google.yaml

```yaml
# Optional owner-approved Google-only egress. Base web/database isolation is retained.
services:
  web:
    environment:
      GOOGLE_OAUTH_CONFIG_FILE: /run/secrets/google_oauth
    secrets: [google_oauth]
    networks:
      google_private:
        ipv4_address: 172.30.20.3
    depends_on:
      google-egress:
        condition: service_healthy
  google-egress:
    image: ${CAMPGROUND_EGRESS_IMAGE:?Set the verified Google egress image digest}
    user: "10001:10001"
    restart: unless-stopped
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    tmpfs:
      - /run/squid:rw,noexec,nosuid,size=4m,mode=0700,uid=10001,gid=10001
      - /tmp:rw,noexec,nosuid,size=4m,mode=0700,uid=10001,gid=10001
    pids_limit: 64
    mem_limit: 128m
    cpus: 0.5
    networks:
      google_edge: {}
      google_private:
        ipv4_address: 172.30.20.2
    healthcheck:
      test: [CMD, /usr/sbin/squid, -k, check, -f, /etc/squid/squid.conf]
      interval: 10s
      timeout: 5s
      retries: 3
networks:
  google_private:
    internal: true
    ipam:
      config:
        - subnet: 172.30.20.0/28
  google_edge: {}
secrets:
  google_oauth:
    file: ${SECRETS_DIR:-./.secrets}/google_oauth.json
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

### encrypt_deployment_snapshot.py

```python
"""Encrypt a bounded database dump from a pipe; never persist or display plaintext."""

import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet


def encrypt_snapshot(source, key_directory: Path, output_directory: Path):
    for directory in (key_directory, output_directory):
        info = directory.lstat()
        if directory.is_symlink() or not directory.is_dir() or info.st_mode & 0o077:
            raise ValueError("Protected snapshot directories required")
    data = source.read(64 * 1024 * 1024 + 1)
    if not data.startswith(b"PGDMP") or len(data) > 64 * 1024 * 1024:
        raise ValueError("Invalid or oversized database snapshot")
    key = Fernet.generate_key()
    with os.fdopen(
        os.open(key_directory / "snapshot.key", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
    ) as stream:
        stream.write(key)
        stream.flush()
        os.fsync(stream.fileno())
    cipher = Fernet(key)
    with os.fdopen(
        os.open(
            output_directory / "database.dump.fernet", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        ),
        "wb",
    ) as stream:
        stream.write(cipher.encrypt(data))
        stream.flush()
        os.fsync(stream.fileno())
    if cipher.decrypt((output_directory / "database.dump.fernet").read_bytes()) != data:
        raise ValueError("Encrypted snapshot verification failed")


if __name__ == "__main__":
    try:
        encrypt_snapshot(sys.stdin.buffer, Path("/recovery-key"), Path("/snapshot"))
        print("Database snapshot encrypted and authenticated decryption verified.")
    except Exception:
        raise SystemExit("Snapshot creation failed; sensitive diagnostics withheld.") from None
```

### images.env

```text
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:f0c68d4a4eba577f8238e2468b80798470c2e50aba9de0da5633ed06dfc07c84
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:4b029479bd88aa2ee6c04ef771945ad7c93d07066afbb776cdccb61deb1ebe3b
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:270cb50798a53012ba565e231011551f0bf157823e1e1e0be41f4aeb60b66617
CAMPGROUND_EGRESS_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:2cc4a5fd75ec1084de1849bff1747c315f7457d7fa2562e6d667574cd29b4830
```

### upgrade_aws_google.sh

```sh
#!/usr/bin/env bash
# Exact, first-enable upgrade for the existing owner-authorized AWS test deployment.
# The caller must disclose this complete script and its image lock before executing it.
set -euo pipefail
umask 077
stage=preflight
trap 'printf "Google upgrade stopped during %s; diagnostics withheld; retain recovery files.\n" "$stage" >&2' ERR
test "$(id -u)" = 0
cd /home/ec2-user/camp-butts-google-upgrade
sha256sum --check bundle.sha256
test -d /opt/camp-butts-test
test ! -e /opt/camp-butts-test/compose.google.yaml
cmp baseline-images.env /opt/camp-butts-test/images.env
test "$(stat -c '%u:%g:%a' /opt/camp-butts-test/.secrets/google_oauth.json)" = 10001:10001:600
test ! -L /opt/camp-butts-test/.secrets/google_oauth.json
docker network inspect $(docker network ls -q) > networks.json
ip -j route show > routes.json
python3 - <<'PY'
import ipaddress
import json
target = ipaddress.ip_network("172.30.20.0/28")
values = [r.get("dst", "default") for r in json.load(open("routes.json"))]
values += [c.get("Subnet", "") for n in json.load(open("networks.json"))
           for c in n.get("IPAM", {}).get("Config") or []]
for value in values:
    if value in ("default", "", "0.0.0.0/0", "::/0"):
        continue
    network = ipaddress.ip_network(value, strict=False)
    if network.version == 4 and target.overlaps(network):
        raise SystemExit("New private OAuth subnet conflicts with an existing route/network.")
PY
dc_old() {
  docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml "$@"
}
dc_old exec -T web python -c 'import django; django.setup(); from django.db import connection; c=connection.cursor(); c.execute("SELECT slug FROM public.campground_tenants ORDER BY slug"); assert c.fetchall()==[("georgia-mountain-fairgrounds",)]; print("Expected single campground confirmed.")'
stage=pulling-reviewed-images
# The bundle image lock is non-secret and generated from verified registry manifests.
while IFS='=' read -r name reference; do
  case "$name" in CAMPGROUND_WEB_IMAGE|CAMPGROUND_DB_IMAGE|CAMPGROUND_PROXY_IMAGE|CAMPGROUND_EGRESS_IMAGE) ;;
    *) exit 1 ;;
  esac
  [[ "$reference" =~ ^docker.io/thecyberbutler/campground-(web|db|proxy)@sha256:[0-9a-f]{64}$ ]]
  docker pull "$reference" >/dev/null 2>&1
done < images.env
new_web=$(awk -F= '$1=="CAMPGROUND_WEB_IMAGE" {print $2}' images.env)
stage=validating-protected-google-configuration
docker run --rm --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges:true --mount type=bind,src=/opt/camp-butts-test/.secrets/google_oauth.json,dst=/run/secrets/google_oauth,readonly -e GOOGLE_OAUTH_CONFIG_FILE=/run/secrets/google_oauth --entrypoint python "$new_web" -c 'from config.google import google_configuration; c=google_configuration(); assert set(c)=={"georgia-mountain-fairgrounds"}; assert c["georgia-mountain-fairgrounds"]["client_id"]=="232928548083-ipnfvophvjhhb8bq0rdcu3iqmpfu8ets.apps.googleusercontent.com"; print("Google configuration validated; secret not displayed.")'
stage=stopping-web-for-consistent-upgrade
dc_old stop web >/dev/null 2>&1
stage=encrypted-preupgrade-snapshot
install -m 0640 -o root -g 10001 encrypt_deployment_snapshot.py /opt/camp-butts-test/encrypt_deployment_snapshot.py
test ! -e /root/camp-butts-google-recovery
test ! -e /opt/camp-butts-test/pre-google-snapshot
install -d -m 0700 -o 10001 -g 10001 /root/camp-butts-google-recovery
install -d -m 0700 -o 10001 -g 10001 /opt/camp-butts-test/pre-google-snapshot
dc_old exec -T db sh -c 'PGPASSWORD="$(cat /run/secrets/admin_password)" pg_dump -U postgres -d campground --format=custom' 2>/dev/null |
  docker run --rm -i --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges:true --memory 512m --pids-limit 32 --mount type=bind,src=/root/camp-butts-google-recovery,dst=/recovery-key --mount type=bind,src=/opt/camp-butts-test/pre-google-snapshot,dst=/snapshot --mount type=bind,src=/opt/camp-butts-test/encrypt_deployment_snapshot.py,dst=/encrypt_snapshot.py,readonly --entrypoint python "$new_web" /encrypt_snapshot.py
stage=installing-reviewed-configuration
install -m 0600 /opt/camp-butts-test/images.env /opt/camp-butts-test/pre-google-snapshot/previous-images.env
install -m 0640 -o root -g 10001 compose.yaml compose.registry.yaml compose.google.yaml images.env check_database_boundary.py /opt/camp-butts-test/
cd /opt/camp-butts-test
dc() {
  docker compose -p camp-butts-test --env-file .env --env-file images.env -f compose.yaml -f compose.registry.yaml -f compose.google.yaml "$@"
}
dc config --quiet
stage=starting-database
dc up -d --no-build --wait --wait-timeout 120 db >/dev/null 2>&1
stage=applying-socialaccount-migrations
dc run --rm --no-deps migrate tenant_command --campground georgia-mountain-fairgrounds migrate --noinput >/dev/null 2>&1
dc run --rm --no-deps provision --grant-runtime --campground georgia-mountain-fairgrounds >/dev/null 2>&1
stage=collecting-static-assets
dc run --rm --no-deps migrate collectstatic --noinput >/dev/null 2>&1
stage=starting-reviewed-google-egress-and-web
dc up -d --no-build --wait --wait-timeout 180 google-egress web proxy >/dev/null 2>&1
stage=validating-runtime
dc exec -T web python manage.py check --deploy --fail-level WARNING >/dev/null 2>&1
dc exec -T web python - --campground georgia-mountain-fairgrounds < check_database_boundary.py
dc exec -T web python - <<'PY'
import django
django.setup()
from django.conf import settings
from apps.google_auth.transport import GoogleSession
assert not settings.DEBUG and settings.APP_ENVIRONMENT == "development"
assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
assert settings.SOCIALACCOUNT_STORE_TOKENS is False
with GoogleSession() as session:
    response = session.get("https://www.googleapis.com/oauth2/v1/certs")
    assert response.status_code == 200 and isinstance(response.json(), dict)
print("Google signing-key HTTPS works through restricted proxy; secure runtime settings retained.")
PY
dc ps --format '{{.Service}} {{.State}} {{.Health}} {{.Publishers}}'
printf '%s\n' 'Google capability deployed. External start/callback controls and owner sign-in still require verification.'
```

### verify_aws_google.sh

```sh
#!/usr/bin/env bash
set -euo pipefail
umask 077
cd /opt/camp-butts-test
dc() {
  docker compose -p camp-butts-test --env-file .env --env-file images.env -f compose.yaml -f compose.registry.yaml -f compose.google.yaml "$@"
}
dc exec -T web python - <<'PY'
import uuid
import django
django.setup()
from django.db import connection, transaction
from apps.accounts.models import User
from apps.tenancy.context import lookup, tenant_scope
from allauth.socialaccount.models import SocialAccount, SocialToken
with tenant_scope(lookup("georgia-mountain-fairgrounds")):
    with transaction.atomic():
        marker = "oauth-boundary-" + uuid.uuid4().hex
        user = User.objects.create_user(username=marker, email=marker + "@example.invalid")
        account = SocialAccount.objects.create(user=user, provider="google", uid=marker)
        account.delete()
        assert not SocialAccount.objects.filter(user=user).exists()
        assert not SocialToken.objects.exists()
        transaction.set_rollback(True)
    assert not User.objects.filter(username=marker).exists()
print("Runtime social-account unlink cascade verified in rolled-back synthetic transaction.")
PY
python3 - <<'PY'
import json
import subprocess

def query(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout
ids = query("docker", "ps", "-q", "--filter", "label=com.docker.compose.project=camp-butts-test").split()
containers = json.loads(query("docker", "inspect", *ids))
services = {c["Config"]["Labels"]["com.docker.compose.service"]: c for c in containers}
assert set(services) == {"web", "db", "proxy", "google-egress"}
for name, c in services.items():
    host = c["HostConfig"]
    assert c["Config"]["User"] == "10001:10001"
    assert host["ReadonlyRootfs"] and not host["Privileged"]
    assert host["CapDrop"] == ["ALL"] and "no-new-privileges:true" in host["SecurityOpt"]
    if name != "proxy":
        assert not host["PortBindings"]
    if name == "google-egress":
        assert all(m["Type"] == "tmpfs" for m in c["Mounts"])
    assert all("docker.sock" not in m.get("Source", "") for m in c["Mounts"])
network_names = {n for c in containers for n in c["NetworkSettings"]["Networks"]}
networks = {n["Name"]: n for n in json.loads(query("docker", "network", "inspect", *network_names))}
for n in services["web"]["NetworkSettings"]["Networks"]:
    assert networks[n]["Internal"]
assert set(services["google-egress"]["NetworkSettings"]["Networks"]) == {"camp-butts-test_google_private", "camp-butts-test_google_edge"}
assert networks["camp-butts-test_google_private"]["Internal"]
assert not networks["camp-butts-test_google_edge"]["Internal"]
assert set(services["db"]["NetworkSettings"]["Networks"]) == {"camp-butts-test_database"}
print("Actual container privilege, network, mount and public-port boundaries verified.")
PY
```

### bundle.sha256

```text
8ca6ada65b4eaf38ab8da8ae2dd1b82af968f5ceeb8a26c0c356f8d8c6cd9edc  baseline-images.env
7d877a4b73c9f05b3a6c16cc345a01154c9a8782ed1cb152fff35bfb6df48664  check_database_boundary.py
6a0407ab08a285a7ba34d001b4ea12310610d04cf2734c419e38b8700ad38fb9  compose.google.yaml
e9ff9a5ba3bde237d5631ebed1cae33da2fed467a1e0e449681199be139571e0  compose.registry.yaml
292f300e9b510be358693aebd2b6e839426b047b70b2b216aa4c7670467c880a  compose.yaml
e7f0c39a9b23489564b2f6bc7db6b2d888939acd0923d7e1134e597371b050e6  encrypt_deployment_snapshot.py
53b055edbfb90ae71af69339fdff113bb960a4f55f37ce33de00dbbaa4934166  images.env
fdfd00b771d118bd9cd95371c04dceb7f786c2226e10d89fc3477c0653623376  upgrade_aws_google.sh
b91e7626b32e77256e1cba2f1100a8629803575875e530a392c909687bdae46f  verify_aws_google.sh
```

## Public validation after the SSH commands

These fixed public probes do not complete Google consent or transmit a real account token.
They retain cookies/state only in process memory and print generic outcomes.

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
```

## Execution status

Executed successfully after disclosure. All bundle hashes and baseline lock matched; the
protected client file passed validation without disclosure. Encrypted DB snapshot creation
and authenticated decryption passed. Vendor socialaccount migrations and forced-RLS/runtime
grants were applied, static assets collected and all four services started. Runtime Django
deployment checks, denied DB operations, real Google signing-key TLS through the proxy,
rolled-back synthetic unlink cascade and actual container/network/port boundaries passed.
Public HTTPS/banner/security-header/CSRF/host/SNI/body-limit probes and Google start/callback/
PKCE/nonce/disabled-token-route probes passed. Real human consent/token exchange/sign-in is
still pending; it is not implied by infrastructure/start-flow checks.

One additional read-only status command was disclosed in chat before execution while the
upgrade was waiting. It reported all four running services, with web/db/egress healthy:

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test "sudo -n docker ps -a --filter label=com.docker.compose.project=camp-butts-test --format '{{.Names}} {{.Status}}'"
```
