#!/bin/sh
set -eu
umask 077
fail() { echo 'Proxy startup refused: check hostname, TLS mode and protected storage.' >&2; exit 1; }
test "$(id -u)" -ne 0 || fail
: "${APP_DOMAIN:?Set the exact HTTPS hostname}"
: "${TLS_MODE:=acme}"
: "${HTTPS_PORT:=443}"
export TLS_MODE HTTPS_PORT
test "${#APP_DOMAIN}" -le 253 || fail
printf '%s' "$APP_DOMAIN" | grep -Eq '^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$' || fail
case "$HTTPS_PORT" in ''|*[!0-9]*) fail ;; esac
test "$HTTPS_PORT" -ge 1 && test "$HTTPS_PORT" -le 65535 || fail
case "$TLS_MODE" in
  acme)
    case "$APP_DOMAIN" in localhost|*.localhost|*.test|*.invalid) fail ;; esac
    test -d /data && test ! -L /data || fail
    test "$(stat -c %a /data)" = 700 || fail
    test ! -L /data/acme.json || fail
    if test ! -e /data/acme.json; then (set -C; : > /data/acme.json); fi
    test -f /data/acme.json && test "$(stat -c %a /data/acme.json)" = 600 || fail
    config=/etc/traefik/traefik.yaml
    ;;
  development)
    test "$APP_DOMAIN" = localhost || fail
    for file in /run/secrets/dev_tls_cert /run/secrets/dev_tls_key; do
      test -f "$file" && test ! -L "$file" && test -r "$file" || fail
      test "$(stat -c %a "$file")" = 600 || fail
    done
    config=/etc/traefik/traefik.dev.yaml
    ;;
  *) fail ;;
esac
exec traefik --configFile="$config"
