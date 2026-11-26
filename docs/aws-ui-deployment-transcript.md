# Exact AWS interface upgrade transcript — 2026-11-25

Prepared and disclosed before execution. Target: the existing owner-authorized development
instance via `ssh camp-butts-test`, release `0.1.0-alpha.20261125-5815b9993895`.
The owner requested “lets scan and deploy” after reviewing the design. No production promotion.

The published release passed source, PostgreSQL, both-architecture image and egress gates.
Prior/new infrastructure filesystem layers and runtime image configurations match on both
architectures; only web content and release labels differ. The live read-only preflight
matched the previous digest lock and all three Compose checksums; all four services were
running and web/DB/egress healthy. Approximately 47 GiB free disk was reported.

The script refuses unexpected baseline configuration, images or runtime boundaries. It checks
migration consistency without applying migrations or grants, stops web briefly, streams a DB
dump directly into authenticated encryption, installs the verified image lock, collects assets,
starts services and validates health, security and booking closure. No secret is transferred,
printed or rotated. Existing TLS/data volumes and Google configuration remain in place.
On an upgrade failure after web stops, the disclosed handler attempts to restore the prior
image lock and static assets without restoring the DB or deleting data. A failed rollback
requires operator attention; raw diagnostics remain withheld.

The host-local encrypted snapshot and separate root-directory key are recovery aids, not
verified off-host disaster recovery. Existing restore/host/production acceptance gates remain.

## Disclosed read-only preflight (completed before upgrade)

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash -s' <<'REMOTE'
set -euo pipefail
cd /opt/camp-butts-test
test -f compose.google.yaml
cat images.env
sha256sum compose.yaml compose.registry.yaml compose.google.yaml
docker compose -p camp-butts-test --env-file .env --env-file images.env -f compose.yaml -f compose.registry.yaml -f compose.google.yaml config --quiet
docker ps --filter label=com.docker.compose.project=camp-butts-test --format '{{.Names}} {{.Status}}'
df -h /opt/camp-butts-test
REMOTE
```

## Exact local SSH/SCP commands

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'umask 077; mkdir /home/ec2-user/camp-butts-ui-5815b9993895'
scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/baseline-images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/baseline-compose.sha256 /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/check_database_boundary.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/encrypt_deployment_snapshot.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/images.env /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/upgrade.sh /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/verify_containers.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/verify_runtime.py /Users/michaelbutler/Repos/camp_butts/.runtime/aws-ui-upgrade-5815b9993895/bundle.sha256 camp-butts-test:/home/ec2-user/camp-butts-ui-5815b9993895/
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n bash /home/ec2-user/camp-butts-ui-5815b9993895/upgrade.sh'
```

## Exact transferred files

### baseline-images.env

```text
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:f0c68d4a4eba577f8238e2468b80798470c2e50aba9de0da5633ed06dfc07c84
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:4b029479bd88aa2ee6c04ef771945ad7c93d07066afbb776cdccb61deb1ebe3b
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:270cb50798a53012ba565e231011551f0bf157823e1e1e0be41f4aeb60b66617
CAMPGROUND_EGRESS_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:2cc4a5fd75ec1084de1849bff1747c315f7457d7fa2562e6d667574cd29b4830
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
CAMPGROUND_WEB_IMAGE=docker.io/thecyberbutler/campground-web@sha256:6fa9602c897b2a1117fb9b1a7d529c346113200bafb6d12cdb8f5988e485f6fe
CAMPGROUND_DB_IMAGE=docker.io/thecyberbutler/campground-db@sha256:776e71237ac4137d7d8ff8388776d402d4c17b7300c9ef1e9dffbd90ae7cbaf4
CAMPGROUND_PROXY_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:0b77b6b27699d5ea9ba1313739b8a9999e3c1dd1d00afed592435b5ba5975a3c
CAMPGROUND_EGRESS_IMAGE=docker.io/thecyberbutler/campground-proxy@sha256:45dab032e5a04ee9c1bc3f6d5574ea9254d1bf58db5b9469a2c1284d44a7ee9f
```

### upgrade.sh

```sh
#!/usr/bin/env bash
# Presentation-only upgrade. No schema changes, grant changes or secret rotation.
set -Eeuo pipefail
umask 077
stage=preflight
stopped=0
bundle=/home/ec2-user/camp-butts-ui-5815b9993895
snapshot=/opt/camp-butts-test/pre-ui-5815b9993895
recovery=/root/camp-butts-ui-recovery-5815b9993895
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
    if dc stop web >/dev/null 2>&1 &&
       install -m 0640 -o root -g 10001 "$bundle/baseline-images.env" /opt/camp-butts-test/images.env &&
       dc up -d --no-build --wait --wait-timeout 120 db >/dev/null 2>&1 &&
       dc run --rm --no-deps migrate collectstatic --noinput >/dev/null 2>&1 &&
       dc up -d --no-build --wait --wait-timeout 180 google-egress web proxy >/dev/null 2>&1; then
      printf '%s\n' 'Previous reviewed release and static assets restored; database and secrets retained.' >&2
    else
      printf '%s\n' 'Rollback requires operator attention; recovery artifacts and volumes retained.' >&2
    fi
  fi
  exit 1
}
trap on_error ERR
test "$(id -u)" = 0
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
dc exec -T web python - < verify_runtime.py
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
        if key != 'CAMPGROUND_WEB_IMAGE':
            assert before['RootFS'] == after['RootFS']
        for image in (before, after):
            image['Config'].pop('Labels', None)
        assert before['Config'] == after['Config']
    print('Infrastructure filesystem layers and all runtime image configurations unchanged.')
except Exception:
    raise SystemExit('Image compatibility check failed; deployment not changed.') from None
PY
new_web=$(awk -F= '$1=="CAMPGROUND_WEB_IMAGE" {print $2}' images.env)
newdc config --quiet
stage=checking-schema-consistency
newdc run --rm --no-deps migrate tenant_command --campground georgia-mountain-fairgrounds migrate --check >/dev/null 2>&1
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
stage=installing-image-lock
install -m 0640 -o root -g 10001 images.env /opt/camp-butts-test/images.env
stage=starting-database
dc up -d --no-build --wait --wait-timeout 120 db >/dev/null 2>&1
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
printf '%s\n' 'UI prerelease deployed and runtime controls verified. Public acceptance probes follow.'
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
    expected = dict(line.split('=', 1) for line in Path('/opt/camp-butts-test/images.env').read_text().splitlines())
    ids = query('docker', 'ps', '-q', '--filter', 'label=com.docker.compose.project=camp-butts-test').split()
    containers = json.loads(query('docker', 'inspect', *ids))
    services = {c['Config']['Labels']['com.docker.compose.service']: c for c in containers}
    assert set(services) == {'web', 'db', 'proxy', 'google-egress'}
    keys = {'web': 'WEB', 'db': 'DB', 'proxy': 'PROXY', 'google-egress': 'EGRESS'}
    for name, c in services.items():
        host = c['HostConfig']
        assert c['Config']['Image'] == expected['CAMPGROUND_' + keys[name] + '_IMAGE']
        assert c['Config']['User'] == '10001:10001'
        assert host['ReadonlyRootfs'] and not host['Privileged']
        assert host['CapDrop'] == ['ALL'] and 'no-new-privileges:true' in host['SecurityOpt']
        assert c['State']['Running']
        if name != 'proxy':
            assert not host['PortBindings']
            assert c['State']['Health']['Status'] == 'healthy'
        else:
            assert set(host['PortBindings']) == {'8080/tcp', '8443/tcp'}
        if name == 'google-egress':
            assert all(m['Type'] == 'tmpfs' for m in c['Mounts'])
        assert all('docker.sock' not in m.get('Source', '') for m in c['Mounts'])
    names = {n for c in containers for n in c['NetworkSettings']['Networks']}
    networks = {n['Name']: n for n in json.loads(query('docker', 'network', 'inspect', *names))}
    assert set(services['web']['NetworkSettings']['Networks']) == {
        'camp-butts-test_application', 'camp-butts-test_database', 'camp-butts-test_google_private'}
    for name in services['web']['NetworkSettings']['Networks']:
        assert networks[name]['Internal']
    assert set(services['google-egress']['NetworkSettings']['Networks']) == {
        'camp-butts-test_google_private', 'camp-butts-test_google_edge'}
    assert networks['camp-butts-test_google_private']['Internal']
    assert not networks['camp-butts-test_google_edge']['Internal']
    assert set(services['db']['NetworkSettings']['Networks']) == {'camp-butts-test_database'}
    assert set(services['proxy']['NetworkSettings']['Networks']) == {
        'camp-butts-test_application', 'camp-butts-test_edge'}
    print('Actual image identities, health, container privileges, networks and public-port boundaries verified.')
except Exception:
    print('Container boundary verification failed; diagnostics withheld.', file=sys.stderr)
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
    assert not settings.DEBUG and settings.APP_ENVIRONMENT == 'development'
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
    assert settings.SOCIALACCOUNT_STORE_TOKENS is False
    with connection.cursor() as cursor:
        cursor.execute('SELECT slug FROM public.campground_tenants ORDER BY slug')
        assert cursor.fetchall() == [('georgia-mountain-fairgrounds',)]
    with tenant_scope(lookup('georgia-mountain-fairgrounds')):
        assert Campground.objects.get(pk=1).booking_enabled is False
        assert not Campsite.objects.filter(active=True).exists()
    with GoogleSession() as session:
        response = session.get('https://www.googleapis.com/oauth2/v1/certs')
        assert response.status_code == 200 and isinstance(response.json(), dict)
    print('Secure development settings, inactive inventory, closed booking and Google TLS verified.')
except Exception:
    print('Runtime verification failed; sensitive diagnostics withheld.', file=sys.stderr)
    raise SystemExit(1) from None
```

### bundle.sha256

```text
53b055edbfb90ae71af69339fdff113bb960a4f55f37ce33de00dbbaa4934166  baseline-images.env
1ebafd576de268057059eef474a774127c750f7df8802176cebf6954a517ce7d  baseline-compose.sha256
7d877a4b73c9f05b3a6c16cc345a01154c9a8782ed1cb152fff35bfb6df48664  check_database_boundary.py
e7f0c39a9b23489564b2f6bc7db6b2d888939acd0923d7e1134e597371b050e6  encrypt_deployment_snapshot.py
ba01a7f52dcb1fd1daad1ad45809b1d5a30e9217283c585e645847d3f06a1bf9  images.env
92accad27ce61b836c3ea146eb4ae7fc7cd8cbf0944d7ac21a8c0cc56d26faa6  upgrade.sh
13f78cff1b4448a7993ae6def46c3e6a145b5af6d74b1369eb470e512037b838  verify_containers.py
552f4ccba0e1f6a36041adb78b022e6a9d0eef4b08546ac836a7190109c86ec9  verify_runtime.py
```

## Public validation after deployment

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
.venv/bin/python .runtime/aws-ui-upgrade-5815b9993895/check_public_ui.py
```

Existing public probes perform fixed HTTPS/header/CSRF/host/SNI/body-size and Google
start/PKCE/nonce/callback checks; they never print cookies, token values or page bodies.
The additional local probe compares deployed CSS/artwork hashes and the reviewed home/login
markers, Google button, red banner and booking closure. Its exact contents follow.

```python
"""Verify deployed UI bytes and presentation without printing cookies or page bodies."""
from pathlib import Path
import hashlib
import sys
import requests

ROOT = Path('/Users/michaelbutler/Repos/camp_butts')
ORIGIN = 'https://camp-butts-test.thecyberbutler.io'
PREFIX = '/c/georgia-mountain-fairgrounds'
try:
    with requests.Session() as browser:
        browser.trust_env = False
        browser.verify = '/etc/ssl/cert.pem'
        for asset in ('css/app.css', 'images/camp-landscape.svg'):
            response = browser.get(ORIGIN + '/static/' + asset, timeout=(5, 15), allow_redirects=False)
            assert response.status_code == 200
            assert hashlib.sha256(response.content).digest() == hashlib.sha256((ROOT / 'static' / asset).read_bytes()).digest()
        for path, marker in ((PREFIX + '/', 'class="hero hero-grid"'), (PREFIX + '/accounts/login/', 'class="account-shell"')):
            response = browser.get(ORIGIN + path, timeout=(5, 15), allow_redirects=False)
            assert response.status_code == 200
            assert marker in response.text
            assert response.content.count(b'THIS IS A TEST INSTANCE') == 1
            if path.endswith('/accounts/login/'):
                assert 'Continue with Google' in response.text
            else:
                assert 'Online reservations are not open.' in response.text
    print('Published CSS/artwork match reviewed source; modern home/login, Google option, banner and booking closure verified.')
except Exception:
    print('Public UI acceptance failed; sensitive diagnostics withheld.', file=sys.stderr)
    raise SystemExit(1) from None
```

## Execution status

Executed successfully after disclosure. Bundle/baseline hashes matched; migration and model
consistency checks passed without applying schema or grant changes. The encrypted database
snapshot and authenticated decryption check passed. Services were updated to the verified
image digests, static assets collected, and all four services are running (web/DB/egress healthy).
Django deployment checks, actual DB privilege/RLS denial probes, private network/container
boundaries, closed booking/inactive drafts and Google signing-key TLS passed. No rollback
was needed; previous images, database/TLS volumes, secrets and recovery artifacts are retained.

Public HTTPS/banner/header/CSRF/host/SNI/body-size probes, Google start/PKCE/nonce/callback
checks and exact deployed CSS/artwork hashes passed. These checks do not claim interactive
Google consent/token exchange or a real user sign-in. Production remains gated.

An additional read-only status command was disclosed before execution while startup health
checks ran. It confirmed all four services running and web/DB/egress healthy:

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test "sudo -n docker ps -a --filter label=com.docker.compose.project=camp-butts-test --format '{{.Names}} {{.Status}}'"
```

This upgrade script deliberately refuses its now-outdated baseline; do not rerun it on the
upgraded host. Future releases require a new reviewed baseline, snapshot path and transcript.
