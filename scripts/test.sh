#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export DATABASE_NAME=campground_test
export DATABASE_USER=campground_test_runner
export DATABASE_HOST=127.0.0.1
export DATABASE_PORT=55432
export DATABASE_PASSWORD_FILE="$PWD/.secrets/database_password"
exec .venv/bin/pytest "$@"
