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
