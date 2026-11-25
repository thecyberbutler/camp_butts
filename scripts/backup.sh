#!/bin/bash
set -euo pipefail
umask 077
: "${RESTIC_REPOSITORY:?Set a protected restic repository}"
: "${RESTIC_PASSWORD_FILE:?Set a protected restic key file}"
: "${PGSERVICEFILE:?Set a protected PostgreSQL service file}"
: "${PGPASSFILE:?Set a protected PostgreSQL password file}"
: "${BACKUP_TENANT_ID:?Set the registered campground UUID}"
: "${BACKUP_TENANT_SCHEMA:?Set its registered PostgreSQL schema}"
: "${BACKUP_CONFIG_DIR:?Set the non-secret deployment configuration directory}"
: "${BACKUP_MEDIA_DIR:?Set the media directory}"
# Select exactly one registered schema. Keep RLS enabled for the read-only backup
# identity; never grant BYPASSRLS or use a database administrator for routine dumps.
[[ "$BACKUP_TENANT_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || exit 1
expected_schema="tenant_${BACKUP_TENANT_ID//-/}"
[[ "$BACKUP_TENANT_SCHEMA" == "$expected_schema" || "$BACKUP_TENANT_SCHEMA" == public ]] || exit 1
export PGOPTIONS="-c app.tenant=$BACKUP_TENANT_ID -c row_security=on"
# Inputs interpolated below have already been restricted to UUID/schema alphabets.
valid="$(psql --dbname=service=campground_backup --no-psqlrc --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 --command="SELECT count(*) FROM public.campground_tenants t \
  JOIN pg_roles r ON r.rolname=current_user WHERE t.id='$BACKUP_TENANT_ID' \
  AND t.schema_name='$BACKUP_TENANT_SCHEMA' AND NOT r.rolsuper AND NOT r.rolbypassrls \
  AND NOT r.rolcreaterole AND NOT r.rolcreatedb \
  AND current_setting('app.tenant')=t.id::text AND current_setting('row_security')='on' \
  AND NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace \
  WHERE n.nspname=t.schema_name AND c.relkind IN ('r','p') \
  AND c.relname NOT IN ('campground_tenants','campground_tenant_events') \
  AND NOT (c.relrowsecurity AND c.relforcerowsecurity))")"
[[ "$valid" == 1 ]] || { echo 'Backup identity or campground boundary validation failed.'; exit 1; }
# libpq reads credentials from protected files; no credential arguments or echo.
# pipefail ensures a failed/partial dump cannot be called a completed backup set.
backup_set="campground-${BACKUP_TENANT_ID}-$(date -u +%Y%m%dT%H%M%SZ)"
pg_dump --dbname=service=campground_backup --format=custom --no-owner --no-acl \
  --enable-row-security --inserts --schema="$BACKUP_TENANT_SCHEMA" \
  --exclude-table=public.campground_tenants \
  --exclude-table=public.campground_tenant_events \
  --exclude-table=public.campground_tenant_events_id_seq |
  restic backup --stdin --stdin-filename campground.dump --tag "$backup_set" --tag database
psql --dbname=service=campground_backup --no-psqlrc --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 --command="SELECT row_to_json(t) FROM public.campground_tenants t \
  WHERE id='$BACKUP_TENANT_ID' AND schema_name='$BACKUP_TENANT_SCHEMA'" |
  restic backup --stdin --stdin-filename campground-registry.json --tag "$backup_set" --tag metadata
restic backup "$BACKUP_CONFIG_DIR" "$BACKUP_MEDIA_DIR" --tag "$backup_set" --tag assets
restic check
printf 'Encrypted backup set completed: %s\n' "$backup_set"
