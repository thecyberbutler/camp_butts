#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
.venv/bin/poetry --version >/dev/null 2>&1 || poetry --version >/dev/null
poetry check --lock
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/pip-audit --progress-spinner off
gitleaks dir . --redact --no-banner
trivy fs --scanners vuln,misconfig,secret --exit-code 1 --severity HIGH,CRITICAL .
