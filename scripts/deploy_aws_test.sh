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
