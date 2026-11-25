FROM python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 POETRY_VIRTUALENVS_IN_PROJECT=true
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.5.2
COPY pyproject.toml poetry.lock ./
RUN poetry sync --only main --no-interaction --no-ansi

FROM python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e
ARG APP_UID=10001
ARG APP_GID=10001
RUN test ${APP_UID} -gt 0 && test ${APP_GID} -gt 0 \
    && addgroup -g ${APP_GID} campground \
    && adduser -D -H -u ${APP_UID} -G campground campground
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings.production
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
# Package installation is a build operation. Remove unused installers and their
# vendored dependencies from both the global and application runtime environments.
RUN /app/.venv/bin/python -m pip uninstall --yes pip \
    && /usr/local/bin/python -m pip uninstall --yes pip
COPY apps ./apps
COPY config ./config
COPY templates ./templates
COPY data/campgrounds ./data/campgrounds
COPY static ./static
COPY manage.py gunicorn.conf.py ./
COPY scripts/entrypoint.sh /app/entrypoint.sh
COPY scripts/provision_database.py scripts/tenant_database.py scripts/runtime_grants.sql /app/scripts/
RUN mkdir /app/staticfiles && chown ${APP_UID}:${APP_GID} /app/staticfiles && chmod 755 /app/entrypoint.sh
USER ${APP_UID}:${APP_GID}
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
