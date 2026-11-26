# Exact AWS email/profile deployment transcript — 2026-11-25

Final reconnection/acceptance work continued on 2026-11-26 (America/New_York).

Prepared before any SSH connection for this deployment. Target: the owner-authorized AWS
test instance through `ssh camp-butts-test`. Release `0.1.0-alpha.20261125-05df000f8652`.
Owner confirmed People API/scopes configured and requested scan/deploy. This is not production.

The four images passed both-platform source/test/vulnerability/secret/egress gates before
publication. Exact digest locks are below. Existing secrets, Compose boundaries, TLS and
volumes remain; no secret file is copied from the workstation or printed. DB/proxy filesystem
layers and all runtime image configurations match the previous release on both architectures.
Web code and the explicitly approved People API proxy allowlist change.

The script checks the sole existing tenant and expected one-migration plan, validates stored
email, stops web, streams a database snapshot directly into authenticated encryption, applies
accounts.0003 under the migrator inside the tenant transaction, compares protected records
in memory, reapplies reviewed grants, collects assets and verifies runtime boundaries.
Old sessions are retired; recent legacy lockouts are preserved with a conservative cooldown.
No account is merged, approved or linked, and no password/MFA/role/verification state changes.
The record comparison excludes intentionally changed identity/session/Axes tables; it separately
checks normalized account/email records and session deletion. No personal records or hashes
are displayed or written to a comparison file. A 10,000-row-per-model bound fails closed.

Only exact reviewed bundle bytes run from a root-owned 0700 directory. A host deployment lock
serializes this upgrade. No scheduled application writer has been configured on this instance.
The application remains stopped if any post-stop step fails. DO NOT restore the prior username
image onto the new schema. Forward fixes require review; destructive restoration requires
separate explicit approval and attention to historical sessions/security state.

Recovery snapshot: `/opt/camp-butts-test/pre-email-05df000f8652/database.dump.fernet`.
Separate key: protected `/root/camp-butts-email-recovery-05df000f8652/` directory.
Authenticated decryption is checked before migration. This is host-local recovery material,
not an off-host backup or a full restore rehearsal. No backup/key bytes appear in this transcript.

## Exact commands, in execution order

### preflight

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -euo pipefail
cd /opt/camp-butts-test
test -f compose.google.yaml
command -v flock >/dev/null
cat images.env
sha256sum compose.yaml compose.registry.yaml compose.google.yaml
docker compose -p camp-butts-test --env-file .env --env-file images.env -f compose.yaml -f compose.registry.yaml -f compose.google.yaml config --quiet
docker ps --filter label=com.docker.compose.project=camp-butts-test --format '{{.Names}} {{.Status}}'
df -h /opt/camp-butts-test
REMOTE
```

### mkdir

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'umask 077; mkdir /home/ec2-user/camp-butts-email-05df000f8652'
```

### copy

```sh
scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/baseline-images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/baseline-compose.sha256 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/check_database_boundary.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/encrypt_deployment_snapshot.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/migrate_email.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/upgrade.sh /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/verify_containers.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/verify_previous_runtime.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/verify_runtime.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/bundle.sha256 camp-butts-test:/home/ec2-user/camp-butts-email-05df000f8652/
```

### execute

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -euo pipefail
umask 077
source_dir=/home/ec2-user/camp-butts-email-05df000f8652
target_dir=/root/camp-butts-email-bundle-05df000f8652
test ! -e "$target_dir"
install -d -m 0700 -o root -g root "$target_dir"
for name in baseline-images.env baseline-compose.sha256 check_database_boundary.py encrypt_deployment_snapshot.py images.env migrate_email.py upgrade.sh verify_containers.py verify_previous_runtime.py verify_runtime.py bundle.sha256; do
  test -f "$source_dir/$name"
  test ! -L "$source_dir/$name"
  install -m 0600 -o root -g root "$source_dir/$name" "$target_dir/$name"
done
cd "$target_dir"
printf '%s\n' '89c0c492ed1cda5ac3a6b214879b67fe258d987e1cf9ba27a92daaa151a12adb  bundle.sha256' | sha256sum --check -
sha256sum --check bundle.sha256
bash ./upgrade.sh
REMOTE
```

## Exact transferred files

### baseline-images.env

```text
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:6fa9602c897b2a1117fb9b1a7d529c346113200bafb6d12cdb8f5988e485f6fe
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:776e71237ac4137d7d8ff8388776d402d4c17b7300c9ef1e9dffbd90ae7cbaf4
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:0b77b6b27699d5ea9ba1313739b8a9999e3c1dd1d00afed592435b5ba5975a3c
CAMPGROUND_EGRESS_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:45dab032e5a04ee9c1bc3f6d5574ea9254d1bf58db5b9469a2c1284d44a7ee9f
```

### baseline-compose.sha256

```text
292f300e9b510be358693aebd2b6e839426b047b70b2b216aa4c7670467c880a  compose.yaml
e9ff9a5ba3bde237d5631ebed1cae33da2fed467a1e0e449681199be139571e0  compose.registry.yaml
6a0407ab08a285a7ba34d001b4ea12310610d04cf2734c419e38b8700ad38fb9  compose.google.yaml
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
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:dab3a656b6bccdb9c97353d0d010027e2e7f7386cbf19079c95642cb50c7f473
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:63bd82a6212ed7dc93b5162b145cf15e78f7ee42adcc08d1bae1ad63ed4ec5a8
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:d3d6b9b2a58e8ac77a5e8981490e631433f7cffcc85e27ccec12561aa15b87b0
CAMPGROUND_EGRESS_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:6efafb6b4b90a6e8eaefb8df4bde6f3d21a3a227572be652bdf15ea0fa4e7d89
```

### migrate_email.py

```python
"""One-time reviewed migration; compare protected records only in process memory."""

import sys

import django
from django.core.validators import validate_email
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.tenancy.context import lookup, tenant_scope


def rows(model):
    result = list(model.objects.order_by("pk").values()[:10001])
    if len(result) > 10000:
        raise ValueError("Bounded migration review required")
    return result


def upgrade(apply=False):
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    if [(m.app_label, m.name, reverse) for m, reverse in plan] != [
        ("accounts", "0003_email_identity", False)
    ]:
        raise ValueError("Unexpected migration plan")
    old_targets = [
        (app, "0002_alter_user_options") if app == "accounts" else (app, name)
        for app, name in targets
    ]
    old = executor.loader.project_state(old_targets).apps
    users = rows(old.get_model("accounts", "User"))
    canonical = {}
    seen = set()
    for user in users:
        email = user["email"].strip().casefold()
        validate_email(email)
        if len(email) > 254 or email in seen:
            raise ValueError("Invalid email identity")
        seen.add(email)
        canonical[user["id"]] = email
    addresses = rows(old.get_model("account", "EmailAddress"))
    for address in addresses:
        if address["email"].strip().casefold() != canonical.get(address["user_id"]):
            raise ValueError("Secondary email review required")
    if not apply:
        return
    changed = {
        "accounts.User",
        "account.EmailAddress",
        "sessions.Session",
        "axes.AccessAttempt",
        "axes.AccessAttemptExpiration",
    }
    preserved = {
        model._meta.label: rows(model)
        for model in old.get_models(include_auto_created=True)
        if model._meta.managed and model._meta.label not in changed
    }
    executor.migrate(targets)
    current = executor.loader.project_state(targets).apps
    for user in users:
        del user["username"]
        user["email"] = canonical[user["id"]]
        user["security_version"] += 1
    for address in addresses:
        address["email"] = canonical[address["user_id"]]
    if rows(current.get_model("accounts", "User")) != users:
        raise ValueError("Account preservation check failed")
    if rows(current.get_model("account", "EmailAddress")) != addresses:
        raise ValueError("Email verification preservation check failed")
    for label, before in preserved.items():
        if rows(current.get_model(label)) != before:
            raise ValueError("Protected data preservation check failed")
    if current.get_model("sessions", "Session").objects.exists():
        raise ValueError("Session retirement failed")
    if MigrationExecutor(connection).migration_plan(targets):
        raise ValueError("Pending migration remains")


def main():
    django.setup()
    if sys.argv[1:] not in (["--check"], ["--apply"]):
        raise ValueError("Explicit operation required")
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user")
        if cursor.fetchone() != ("campground_migrator",):
            raise ValueError("Migration identity required")
        cursor.execute("SELECT slug, active FROM public.campground_tenants ORDER BY slug")
        if cursor.fetchall() != [("georgia-mountain-fairgrounds", True)]:
            raise ValueError("Unexpected campground inventory")
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        upgrade(apply=sys.argv[1] == "--apply")
    print(
        "Email migration and protected-data comparison passed."
        if sys.argv[1] == "--apply"
        else "Email migration prerequisites passed; no data changed."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(
            "Email migration validation failed; sensitive diagnostics withheld."
        ) from None
```

### upgrade.sh

```sh
#!/usr/bin/env bash
# Email identity migration and approved Google profile deployment; no secret rotation.
set -Eeuo pipefail
umask 077
stage=preflight
stopped=0
bundle=/root/camp-butts-email-bundle-05df000f8652
snapshot=/opt/camp-butts-test/pre-email-05df000f8652
recovery=/root/camp-butts-email-recovery-05df000f8652
dc() {
  docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml "$@"
}
newdc() {
  docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file "$bundle/images.env" -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml "$@"
}
on_error() {
  trap - ERR
  set +e
  printf 'Upgrade stopped during %s; raw diagnostics withheld.\n' "$stage" >&2
  if [ "$stopped" = 1 ]; then
    dc stop web >/dev/null 2>&1
    printf '%s\n' 'Web remains stopped. Preserve all data and recovery artifacts; use a reviewed forward fix. Never restart a username-based image after migration.' >&2
  fi
  exit 1
}
trap on_error ERR
test "$(id -u)" = 0
exec 9>/run/lock/camp-butts-deploy.lock
flock -n 9
cd "$bundle"
sha256sum --check bundle.sha256
cmp baseline-images.env /opt/camp-butts-test/images.env
(cd /opt/camp-butts-test && sha256sum --check "$bundle/baseline-compose.sha256")
test ! -e "$snapshot"
test ! -e "$recovery"
test "$(stat -c '%u:%g:%a' /opt/camp-butts-test/.secrets/google_oauth.json)" = 10001:10001:600
test ! -L /opt/camp-butts-test/.secrets/google_oauth.json
dc config --quiet
python3 verify_containers.py
dc exec -T web python - < verify_previous_runtime.py
stage=pulling-reviewed-images
while IFS='=' read -r name reference; do
  case "$name" in CAMPGROUND_WEB_IMAGE|CAMPGROUND_DB_IMAGE|CAMPGROUND_PROXY_IMAGE|CAMPGROUND_EGRESS_IMAGE) ;; *) exit 1 ;; esac
  [[ "$reference" =~ ^docker.io/thecyberbutler/campground-(web|db|proxy)@sha256:[0-9a-f]{64}$ ]]
  docker pull "$reference" >/dev/null 2>&1
done < images.env
stage=checking-unchanged-infrastructure
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

def read(name):
    return dict(line.split('=', 1) for line in Path(name).read_text().splitlines())

def inspect(ref):
    return json.loads(subprocess.run(['docker', 'image', 'inspect', ref], check=True, capture_output=True, text=True).stdout)[0]

try:
    old, new = read('baseline-images.env'), read('images.env')
    assert set(old) == set(new) == {'CAMPGROUND_WEB_IMAGE', 'CAMPGROUND_DB_IMAGE', 'CAMPGROUND_PROXY_IMAGE', 'CAMPGROUND_EGRESS_IMAGE'}
    for key in old:
        before, after = inspect(old[key]), inspect(new[key])
        if key in ('CAMPGROUND_DB_IMAGE', 'CAMPGROUND_PROXY_IMAGE'):
            assert before['RootFS'] == after['RootFS']
        for image in (before, after):
            image['Config'].pop('Labels', None)
        assert before['Config'] == after['Config']
    print('Database/proxy filesystem layers and all runtime image configurations unchanged; web and approved Google allowlist differ.')
except Exception:
    raise SystemExit('Image compatibility check failed; deployment not changed.') from None
PY
new_web=$(awk -F= '$1=="CAMPGROUND_WEB_IMAGE" {print $2}' images.env)
newdc config --quiet
stage=checking-email-migration-prerequisites
newdc run --rm -T --no-deps --entrypoint python migrate - --check < migrate_email.py
newdc run --rm --no-deps migrate tenant_command --campground georgia-mountain-fairgrounds makemigrations --check --dry-run >/dev/null 2>&1
stage=stopping-web-for-snapshot
stopped=1
dc stop web >/dev/null 2>&1
stage=encrypted-preupgrade-snapshot
install -d -m 0700 -o 10001 -g 10001 "$recovery" "$snapshot"
install -m 0640 -o root -g 10001 encrypt_deployment_snapshot.py "$snapshot/encrypt_deployment_snapshot.py"
install -m 0600 baseline-images.env "$snapshot/previous-images.env"
dc exec -T db sh -c 'PGPASSWORD="$(cat /run/secrets/admin_password)" pg_dump -U postgres -d campground --format=custom' 2>/dev/null |
  docker run --rm -i --network none --read-only --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges:true --memory 512m --pids-limit 32 --mount "type=bind,src=$recovery,dst=/recovery-key" --mount "type=bind,src=$snapshot,dst=/snapshot" --mount "type=bind,src=$snapshot/encrypt_deployment_snapshot.py,dst=/encrypt_snapshot.py,readonly" --entrypoint python "$new_web" /encrypt_snapshot.py
stage=migrating-email-identity
newdc run --rm -T --no-deps --entrypoint python migrate - --apply < migrate_email.py
stage=installing-image-lock
install -m 0640 -o root -g 10001 images.env /opt/camp-butts-test/images.env
stage=starting-database
dc up -d --no-build --wait --wait-timeout 120 db >/dev/null 2>&1
stage=reapplying-reviewed-grants
dc run --rm --no-deps provision --grant-runtime --campground georgia-mountain-fairgrounds >/dev/null 2>&1
stage=checking-migrated-schema
dc run --rm --no-deps migrate tenant_command --campground georgia-mountain-fairgrounds migrate --check >/dev/null 2>&1
stage=collecting-static-assets
dc run --rm --no-deps migrate collectstatic --noinput >/dev/null 2>&1
stage=starting-services
dc up -d --no-build --wait --wait-timeout 180 google-egress web proxy >/dev/null 2>&1
stage=validating-deployment
dc exec -T web python manage.py check --deploy --fail-level WARNING >/dev/null 2>&1
dc exec -T web python - --campground georgia-mountain-fairgrounds < check_database_boundary.py
dc exec -T web python - < verify_runtime.py
python3 verify_containers.py
stopped=0
dc ps --format '{{.Service}} {{.State}} {{.Health}} {{.Publishers}}'
printf '%s\n' 'Email/profile prerelease deployed; migration, preservation and runtime controls verified. Public acceptance probes follow.'
```

### verify_containers.py

```python
"""Inspect actual container boundaries; print no configuration or credentials."""

import json
import subprocess
import sys
from pathlib import Path


def query(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


try:
    expected = dict(
        line.split("=", 1)
        for line in Path("/opt/camp-butts-test/images.env").read_text().splitlines()
    )
    ids = query(
        "docker", "ps", "-q", "--filter", "label=com.docker.compose.project=camp-butts-test"
    ).split()
    containers = json.loads(query("docker", "inspect", *ids))
    services = {c["Config"]["Labels"]["com.docker.compose.service"]: c for c in containers}
    assert set(services) == {"web", "db", "proxy", "google-egress"}
    keys = {"web": "WEB", "db": "DB", "proxy": "PROXY", "google-egress": "EGRESS"}
    for name, c in services.items():
        host = c["HostConfig"]
        assert c["Config"]["Image"] == expected["CAMPGROUND_" + keys[name] + "_IMAGE"]
        assert c["Config"]["User"] == "10001:10001"
        assert host["ReadonlyRootfs"] and not host["Privileged"]
        assert host["CapDrop"] == ["ALL"] and "no-new-privileges:true" in host["SecurityOpt"]
        assert c["State"]["Running"]
        if name != "proxy":
            assert not host["PortBindings"]
            assert c["State"]["Health"]["Status"] == "healthy"
        else:
            assert set(host["PortBindings"]) == {"8080/tcp", "8443/tcp"}
        if name == "google-egress":
            assert all(m["Type"] == "tmpfs" for m in c["Mounts"])
        assert all("docker.sock" not in m.get("Source", "") for m in c["Mounts"])
    names = {n for c in containers for n in c["NetworkSettings"]["Networks"]}
    networks = {n["Name"]: n for n in json.loads(query("docker", "network", "inspect", *names))}
    assert set(services["web"]["NetworkSettings"]["Networks"]) == {
        "camp-butts-test_application",
        "camp-butts-test_database",
        "camp-butts-test_google_private",
    }
    for name in services["web"]["NetworkSettings"]["Networks"]:
        assert networks[name]["Internal"]
    assert set(services["google-egress"]["NetworkSettings"]["Networks"]) == {
        "camp-butts-test_google_private",
        "camp-butts-test_google_edge",
    }
    assert networks["camp-butts-test_google_private"]["Internal"]
    assert not networks["camp-butts-test_google_edge"]["Internal"]
    assert set(services["db"]["NetworkSettings"]["Networks"]) == {"camp-butts-test_database"}
    assert set(services["proxy"]["NetworkSettings"]["Networks"]) == {
        "camp-butts-test_application",
        "camp-butts-test_edge",
    }
    print(
        "Actual image identities, health, container privileges, networks and public-port boundaries verified."
    )
except Exception:
    print("Container boundary verification failed; diagnostics withheld.", file=sys.stderr)
    raise SystemExit(1) from None
```

### verify_previous_runtime.py

```python
"""Validate runtime settings and closed booking without disclosing account data."""

import sys

try:
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from apps.tenancy.context import lookup, tenant_scope
    from apps.configuration.models import Campground
    from apps.campsites.models import Campsite
    from apps.google_auth.transport import GoogleSession

    assert not settings.DEBUG and settings.APP_ENVIRONMENT == "development"
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
    assert settings.SOCIALACCOUNT_STORE_TOKENS is False
    with connection.cursor() as cursor:
        cursor.execute("SELECT slug FROM public.campground_tenants ORDER BY slug")
        assert cursor.fetchall() == [("georgia-mountain-fairgrounds",)]
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        assert Campground.objects.get(pk=1).booking_enabled is False
        assert not Campsite.objects.filter(active=True).exists()
    with GoogleSession() as session:
        response = session.get("https://www.googleapis.com/oauth2/v1/certs")
        assert response.status_code == 200 and isinstance(response.json(), dict)
    print(
        "Secure development settings, inactive inventory, closed booking and Google TLS verified."
    )
except Exception:
    print("Runtime verification failed; sensitive diagnostics withheld.", file=sys.stderr)
    raise SystemExit(1) from None
```

### verify_runtime.py

```python
"""Validate runtime settings and closed booking without disclosing account data."""

import sys

try:
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from apps.tenancy.context import lookup, tenant_scope
    from apps.configuration.models import Campground
    from apps.campsites.models import Campsite
    from apps.google_auth.transport import GoogleSession

    assert not settings.DEBUG and settings.APP_ENVIRONMENT == "development"
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
    assert settings.SOCIALACCOUNT_STORE_TOKENS is False
    with connection.cursor() as cursor:
        cursor.execute("SELECT slug FROM public.campground_tenants ORDER BY slug")
        assert cursor.fetchall() == [("georgia-mountain-fairgrounds",)]
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        assert Campground.objects.get(pk=1).booking_enabled is False
        assert not Campsite.objects.filter(active=True).exists()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s",
                ["accounts_user"],
            )
            columns = {row[0] for row in cursor.fetchall()}
            assert "email" in columns and "username" not in columns
    with GoogleSession() as session:
        response = session.get("https://www.googleapis.com/oauth2/v1/certs")
        assert response.status_code == 200 and isinstance(response.json(), dict)
    from apps.accounts.models import User
    from apps.google_auth.constants import GOOGLE_SCOPES, PEOPLE_SELF_URL

    assert User.USERNAME_FIELD == "email" and User.username is None
    assert settings.ACCOUNT_USER_MODEL_USERNAME_FIELD is None
    assert settings.ACCOUNT_LOGIN_METHODS == {"email"}
    assert len(GOOGLE_SCOPES) == 4 and "profile" in GOOGLE_SCOPES
    with GoogleSession() as session:
        response = session.get(PEOPLE_SELF_URL)
        assert response.status_code in (401, 403)
    print(
        "Email identity, secure settings, closed booking, Google certificates and unauthenticated People TLS verified."
    )
except Exception:
    print("Runtime verification failed; sensitive diagnostics withheld.", file=sys.stderr)
    raise SystemExit(1) from None
```

### bundle.sha256

```text
ba01a7f52dcb1fd1daad1ad45809b1d5a30e9217283c585e645847d3f06a1bf9  baseline-images.env
1ebafd576de268057059eef474a774127c750f7df8802176cebf6954a517ce7d  baseline-compose.sha256
7d877a4b73c9f05b3a6c16cc345a01154c9a8782ed1cb152fff35bfb6df48664  check_database_boundary.py
e7f0c39a9b23489564b2f6bc7db6b2d888939acd0923d7e1134e597371b050e6  encrypt_deployment_snapshot.py
4a518de3dfdc1d65335aaf2270d3cd742722882d452764608f49495ba37c5ccf  images.env
acb1615731dfcab188eaa3d863e0810b491433be13bd5c9d75277f63d97cb00e  migrate_email.py
4d40d8bcf89e316152b61c6d9ceda6d9f675a713aef78de26943e40a8ce6af29  upgrade.sh
353500b78de747dddf32831deebb8aa34d096b457c78082c5d901a0bdb07ac5f  verify_containers.py
fef0a725f879b6b939426246e33a8041c2d19b0ab4779905cc7b658f7fd05b21  verify_previous_runtime.py
07c213c45e02a12cf2551b6252db8aa2b4466b9d80d525650f136a4d39987ab5  verify_runtime.py
```

## Public acceptance commands (local workstation, after remote upgrade)

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
.venv/bin/python .runtime/aws-email-upgrade-05df000f8652/check_public_ui.py
```

The repository probes are included in the scanned release source. The exact additional
public form/asset probe is below. Responses/cookies/OAuth state are never printed; no user
login, account approval or reservation is performed by these probes.

```python
"""Verify deployed UI bytes and presentation without printing cookies or page bodies."""

from pathlib import Path
import hashlib
import sys
import requests

ROOT = Path("/Users/michaelbutler/Repos/camp_butts")
ORIGIN = "https://camp-butts-test.thecyberbutler.io"
PREFIX = "/c/georgia-mountain-fairgrounds"
try:
    with requests.Session() as browser:
        browser.trust_env = False
        browser.verify = "/etc/ssl/cert.pem"
        for asset in ("css/app.css", "images/camp-landscape.svg"):
            response = browser.get(
                ORIGIN + "/static/" + asset, timeout=(5, 15), allow_redirects=False
            )
            assert response.status_code == 200
            assert (
                hashlib.sha256(response.content).digest()
                == hashlib.sha256((ROOT / "static" / asset).read_bytes()).digest()
            )
        for path, marker in (
            (PREFIX + "/", 'class="hero hero-grid"'),
            (PREFIX + "/accounts/login/", 'class="account-shell"'),
            (PREFIX + "/accounts/signup/", 'class="account-shell"'),
        ):
            response = browser.get(ORIGIN + path, timeout=(5, 15), allow_redirects=False)
            assert response.status_code == 200
            assert marker in response.text
            assert response.content.count(b"THIS IS A TEST INSTANCE") == 1
            assert 'name="username"' not in response.text
            if "/accounts/" in path:
                assert "Continue with Google" in response.text
            else:
                assert "Online reservations are not open." in response.text
    print(
        "Published assets, email-only login/signup forms, Google option, test banner and booking closure verified."
    )
except Exception:
    print("Public UI acceptance failed; sensitive diagnostics withheld.", file=sys.stderr)
    raise SystemExit(1) from None
```

## Predeployment wrapper validation

Three synthetic PostgreSQL checks passed: unchanged preflight then successful preservation,
secondary-email refusal, and transaction rollback on a forced preservation mismatch.
Initial test-loader and deferred-constraint teardown problems were corrected in the private
harness, without changing migration/security logic. Tests did not use live account data.

## Execution status

Prepared; no SSH connection or live mutation has occurred yet. Results will be appended after
execution without changing the disclosed command/script blocks. Any necessary additional
remote command will be disclosed separately before execution.

## Preserved synthetic wrapper test harness

These files were local-only, not transferred to AWS. Run from the repository root with
the protected synthetic PostgreSQL available:

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh .runtime/aws-email-upgrade-05df000f8652/test_migrate_email.py -q --assert=plain --tb=no --show-capture=no
```

### conftest.py

```python
import runpy

for name, value in runpy.run_path("tests/conftest.py").items():
    if not name.startswith("__"):
        globals()[name] = value
```

### test_migrate_email.py

```python
import runpy
import pytest
from django.db import connection, transaction

legacy_schema = runpy.run_path("tests/security/test_email_identity.py")["legacy_schema"]
module = runpy.run_path(".runtime/aws-email-upgrade-05df000f8652/migrate_email.py")
upgrade = module["upgrade"]
pytestmark = pytest.mark.django_db


def test_deployment_migration_preserves_protected_data():
    with legacy_schema() as old:
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        user = old.get_model("accounts", "User").objects.create(
            username="synthetic", email="Synthetic@Example.Test"
        )
        old.get_model("account", "EmailAddress").objects.create(
            user_id=user.pk, email="Synthetic@Example.Test", primary=True, verified=True
        )
        upgrade()
        assert old.get_model("accounts", "User").objects.get(pk=user.pk).username == "synthetic"
        upgrade(apply=True)
        from apps.accounts.models import User

        assert User.objects.get(pk=user.pk).email == "synthetic@example.test"
        with pytest.raises(ValueError, match="Unexpected migration plan"):
            upgrade()


def test_deployment_preflight_refuses_secondary_email():
    with legacy_schema() as old:
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        user = old.get_model("accounts", "User").objects.create(
            username="synthetic", email="synthetic@example.test"
        )
        old.get_model("account", "EmailAddress").objects.create(
            user_id=user.pk, email="other@example.test"
        )
        with pytest.raises(ValueError, match="Secondary email"):
            upgrade()
        assert old.get_model("accounts", "User").objects.get(pk=user.pk).username == "synthetic"


def test_deployment_preservation_failure_rolls_back(monkeypatch):
    with legacy_schema() as old:
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        user = old.get_model("accounts", "User").objects.create(
            username="synthetic", email="Synthetic@Example.Test"
        )
        original = upgrade.__globals__["rows"]

        def mismatch(model):
            result = original(model)
            if model._meta.label == "accounts.User" and not any(
                f.name == "username" for f in model._meta.fields
            ):
                result[0]["approved"] = not result[0]["approved"]
            return result

        monkeypatch.setitem(upgrade.__globals__, "rows", mismatch)
        with pytest.raises(ValueError, match="preservation"), transaction.atomic():
            upgrade(apply=True)
        assert old.get_model("accounts", "User").objects.get(pk=user.pk).username == "synthetic"
```


## Disclosed probe correction and forward recovery

The initial deployment applied the migration and passed protected-data and runtime DB checks.
Its final probe incorrectly expected GoogleSession to return an unauthenticated 401/403,
although that transport intentionally raises for all non-200 responses. The failure handler
stopped web. No authentication, TLS or application behavior is changed to make this pass.
The corrected token-free infrastructure probe uses verified HTTPS, the same proxy/fixed URL,
no redirects, bounded timeouts, streaming and no response-body consumption. This is the same
unauthenticated status expectation already exercised by the disposable proxy release gate.

The following additional commands and full probe are disclosed before reconnection. They
restart only the new migrated release and repeat deployment/DB/container/runtime checks.
They do not rerun migration, restore data or replace the original disclosed bundle.

### Recovery copy

```sh
scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-email-upgrade-05df000f8652/verify_runtime_v2.py camp-butts-test:/home/ec2-user/camp-butts-email-05df000f8652/
```

### Recovery execute

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -Eeuo pipefail
umask 077
exec 9>/run/lock/camp-butts-deploy.lock
flock -n 9
cd /root/camp-butts-email-bundle-05df000f8652
sha256sum --check bundle.sha256
cmp images.env /opt/camp-butts-test/images.env
(cd /opt/camp-butts-test && sha256sum --check /root/camp-butts-email-bundle-05df000f8652/baseline-compose.sha256)
test ! -e verify_runtime_v2.py
test -f /home/ec2-user/camp-butts-email-05df000f8652/verify_runtime_v2.py
test ! -L /home/ec2-user/camp-butts-email-05df000f8652/verify_runtime_v2.py
install -m 0600 -o root -g root /home/ec2-user/camp-butts-email-05df000f8652/verify_runtime_v2.py ./verify_runtime_v2.py
printf '%s\n' '290b377bfc696fb0efbdf37abbbceb46742c96e8ae4c3e8afb48dc6cd3f145c0  verify_runtime_v2.py' | sha256sum --check -
dc() {
  docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml "$@"
}
on_error() {
  trap - ERR
  dc stop web >/dev/null 2>&1 || true
  printf '%s\n' 'Validation failed; web stopped, data preserved, raw diagnostics withheld.' >&2
  exit 1
}
trap on_error ERR
dc up -d --no-deps --no-build --wait --wait-timeout 180 web >/dev/null 2>&1
dc exec -T web python manage.py check --deploy --fail-level WARNING >/dev/null 2>&1
dc exec -T web python - --campground georgia-mountain-fairgrounds < check_database_boundary.py
dc exec -T web python - < verify_runtime_v2.py
python3 verify_containers.py
dc ps --format '{{.Service}} {{.State}} {{.Health}} {{.Publishers}}'
printf '%s\n' 'Email/profile release running; corrected probe and security boundaries passed.'
REMOTE
```

### verify_runtime_v2.py

```python
"""Validate runtime settings and closed booking without disclosing account data."""

import sys

try:
    import django

    django.setup()
    from django.conf import settings
    from django.db import connection
    from apps.tenancy.context import lookup, tenant_scope
    from apps.configuration.models import Campground
    from apps.campsites.models import Campsite
    from apps.google_auth.transport import GoogleSession

    assert not settings.DEBUG and settings.APP_ENVIRONMENT == "development"
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
    assert settings.SOCIALACCOUNT_STORE_TOKENS is False
    with connection.cursor() as cursor:
        cursor.execute("SELECT slug FROM public.campground_tenants ORDER BY slug")
        assert cursor.fetchall() == [("georgia-mountain-fairgrounds",)]
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        assert Campground.objects.get(pk=1).booking_enabled is False
        assert not Campsite.objects.filter(active=True).exists()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=%s",
                ["accounts_user"],
            )
            columns = {row[0] for row in cursor.fetchall()}
            assert "email" in columns and "username" not in columns
    with GoogleSession() as session:
        response = session.get("https://www.googleapis.com/oauth2/v1/certs")
        assert response.status_code == 200 and isinstance(response.json(), dict)
    from apps.accounts.models import User
    from apps.google_auth.constants import GOOGLE_SCOPES, PEOPLE_SELF_URL

    assert User.USERNAME_FIELD == "email" and User.username is None
    assert settings.ACCOUNT_USER_MODEL_USERNAME_FIELD is None
    assert settings.ACCOUNT_LOGIN_METHODS == {"email"}
    assert len(GOOGLE_SCOPES) == 4 and "profile" in GOOGLE_SCOPES
    # The application GoogleSession deliberately rejects every non-200 response.
    # This token-free connectivity probe expects 401/403; no response body is consumed.
    import requests

    with requests.Session() as session:
        session.trust_env = False
        with session.get(
            PEOPLE_SELF_URL,
            proxies={"https": "http://google-egress:3128"},
            verify=True,
            allow_redirects=False,
            timeout=(3.05, 10),
            stream=True,
        ) as response:
            assert response.status_code in (401, 403)
    print(
        "Email identity, secure settings, closed booking, Google certificates and unauthenticated People TLS verified."
    )
except Exception:
    print("Runtime verification failed; sensitive diagnostics withheld.", file=sys.stderr)
    raise SystemExit(1) from None
```

## Disclosed connection-reset diagnostics and final verification — 2026-11-26

SSH reset before the recovery result was received. The disclosed read-only diagnostic
reported all four services running, web/DB/egress healthy, the expected new image-lock hash,
and the deployment lock free. This alone is not treated as complete acceptance.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -euo pipefail
cd /opt/camp-butts-test
sha256sum images.env
docker ps -a --filter label=com.docker.compose.project=camp-butts-test --format '{{.Names}} {{.Status}}'
free -m
uptime
if flock -n /run/lock/camp-butts-deploy.lock -c 'true'; then
  printf '%s\n' 'Deployment lock is free.'
else
  printf '%s\n' 'Deployment command still holds its lock.'
fi
REMOTE
```

The following additional read-only verification is disclosed before execution. No migration,
restart or database restoration is performed.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -euo pipefail
cd /root/camp-butts-email-bundle-05df000f8652
sha256sum --check bundle.sha256
printf '%s\n' '290b377bfc696fb0efbdf37abbbceb46742c96e8ae4c3e8afb48dc6cd3f145c0  verify_runtime_v2.py' | sha256sum --check -
cmp images.env /opt/camp-butts-test/images.env
dc() {
  docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml "$@"
}
dc config --quiet
dc exec -T web python manage.py check --deploy --fail-level WARNING >/dev/null 2>&1
dc exec -T web python - --campground georgia-mountain-fairgrounds < check_database_boundary.py
dc exec -T web python - < verify_runtime_v2.py
python3 verify_containers.py
dc ps --format '{{.Service}} {{.State}} {{.Health}} {{.Publishers}}'
REMOTE
```

### Final verification with explicit stdin isolation

The prior SSH check returned zero without the expected completion output. Because Docker
exec can consume the stdin carrying a `bash -s` transcript, that zero status is not accepted
as proof that every remaining command ran. Repeat with explicit stdin redirection and a final
completion marker. No application control or test assertion is removed.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -euo pipefail
cd /root/camp-butts-email-bundle-05df000f8652
sha256sum --check bundle.sha256
printf '%s\n' '290b377bfc696fb0efbdf37abbbceb46742c96e8ae4c3e8afb48dc6cd3f145c0  verify_runtime_v2.py' | sha256sum --check -
cmp images.env /opt/camp-butts-test/images.env
dc() {
  docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml "$@"
}
dc config --quiet </dev/null
dc exec -T web python manage.py check --deploy --fail-level WARNING </dev/null >/dev/null 2>&1
dc exec -T web python - --campground georgia-mountain-fairgrounds < check_database_boundary.py
dc exec -T web python - < verify_runtime_v2.py
python3 verify_containers.py </dev/null
dc ps --format '{{.Service}} {{.State}} {{.Health}} {{.Publishers}}' </dev/null
printf '%s\n' 'All postflight checks completed.'
REMOTE
```

## Final execution results — 2026-11-26

Completed. Initial preflight matched the previous lock/Compose checksums. The encrypted
snapshot and authenticated-decryption check passed; accounts.0003 and protected-record
comparisons passed, followed by reviewed grants and static collection. The first final probe
failed on its incorrect non-200 expectation, so web stopped. The disclosed corrected probe
and forward restart preserved the migrated schema and all data. SSH disconnected before
its completion result; no success was inferred. Read-only diagnostics found the new images
healthy. A subsequent zero exit without completion output was also not accepted because
Docker could consume shell stdin. The final explicitly redirected verification printed:

- Runtime database boundary verified; all protected operations denied.
- Email identity, secure settings, closed booking, Google certificates and unauthenticated People TLS verified.
- Actual image identities, health, container privileges, networks and public-port boundaries verified.
- All postflight checks completed.

All four services run; web, DB and egress are healthy. Only Traefik publishes 80/443. Public
HTTPS/banner/static/header/CSRF/host/SNI/body-limit checks passed. Public Google start/scopes/
PKCE/nonce/invalid-callback/token-route checks and asset/email-only-form probes passed.
Human Google consent/token exchange/profile import/approved-user login remain unverified.
No database restore, old-image rollback, credential disclosure/rotation or control weakening
occurred. This test deployment does not satisfy the remaining production acceptance gates.
