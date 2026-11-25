"""Deployment labels affect presentation only; they never relax security settings."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def validate_environment(value: str) -> str:
    if value not in {"production", "development", "test"}:
        raise ImproperlyConfigured("APP_ENVIRONMENT must be production, development or test.")
    return value


def deployment_context(request=None):
    return {"show_test_banner": settings.APP_ENVIRONMENT in {"development", "test"}}
