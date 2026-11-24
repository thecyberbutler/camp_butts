#!/bin/sh
set -eu
umask 077
python manage.py check --deploy --fail-level WARNING
exec gunicorn -c gunicorn.conf.py config.wsgi:application
