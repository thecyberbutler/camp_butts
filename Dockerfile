FROM python:3.13-slim-bookworm@sha256:f0fa218d5b06f9b9235024fa061cde2cb141f726de52134471053d2d9b5324a3 AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 POETRY_VIRTUALENVS_IN_PROJECT=true
WORKDIR /app
RUN pip install --no-cache-dir poetry==2.5.2
COPY pyproject.toml poetry.lock ./
RUN poetry sync --only main --no-interaction --no-ansi

FROM python:3.13-slim-bookworm@sha256:f0fa218d5b06f9b9235024fa061cde2cb141f726de52134471053d2d9b5324a3
ARG APP_UID=10001
ARG APP_GID=10001
RUN groupadd --gid ${APP_GID} campground && useradd --uid ${APP_UID} --gid ${APP_GID} --no-create-home campground
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings.production
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY apps ./apps
COPY config ./config
COPY templates ./templates
COPY static ./static
COPY manage.py gunicorn.conf.py ./
COPY scripts/entrypoint.sh /app/entrypoint.sh
COPY scripts/provision_database.py scripts/runtime_grants.sql /app/scripts/
RUN mkdir /app/staticfiles && chown ${APP_UID}:${APP_GID} /app/staticfiles && chmod 755 /app/entrypoint.sh
USER ${APP_UID}:${APP_GID}
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
