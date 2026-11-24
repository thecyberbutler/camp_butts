#!/bin/bash
set -euo pipefail
umask 077
: "${RESTIC_REPOSITORY:?Set the backup repository}"
: "${RESTIC_PASSWORD_FILE:?Set the separately protected key file}"
: "${CONFIRM_ISOLATED_RESTORE:?Set to YES after checking the destination}"
test "$CONFIRM_ISOLATED_RESTORE" = YES
test "$#" -eq 2 || { echo 'Usage: restore.sh SNAPSHOT NEW_ABSOLUTE_STAGING_DIRECTORY'; exit 1; }
case "$2" in /*) ;; *) echo 'Absolute staging directory required'; exit 1 ;; esac
test ! -e "$2" || { echo 'Refusing to overwrite an existing destination'; exit 1; }
mkdir -m 700 "$2"
restic check
restic restore "$1" --target "$2" --verify
echo 'Restored into isolated staging only. Follow the documented database and session revocation procedure.'
