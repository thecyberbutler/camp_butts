#!/bin/bash
set -euo pipefail
umask 077
: "${RESTIC_REPOSITORY:?Set a protected restic repository}"
: "${RESTIC_PASSWORD_FILE:?Set a protected restic key file}"
: "${PGSERVICEFILE:?Set a protected PostgreSQL service file}"
: "${PGPASSFILE:?Set a protected PostgreSQL password file}"
: "${BACKUP_CONFIG_DIR:?Set the non-secret deployment configuration directory}"
: "${BACKUP_MEDIA_DIR:?Set the media directory}"
# libpq reads credentials from protected files; no credential arguments or echo.
# pipefail ensures a pg_dump failure cannot be reported as a successful backup.
backup_set="campground-$(date -u +%Y%m%dT%H%M%SZ)"
pg_dump --dbname=service=campground_backup --format=custom |
  restic backup --stdin --stdin-filename campground.dump --tag "$backup_set" --tag database
restic backup "$BACKUP_CONFIG_DIR" "$BACKUP_MEDIA_DIR" --tag "$backup_set" --tag assets
restic check
printf 'Encrypted backup set completed: %s\n' "$backup_set"
