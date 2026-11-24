import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if os.environ.get("DJANGO_DEBUG", "false").lower() != "false":
    raise ImproperlyConfigured("DEBUG is forbidden")
if DATABASES["default"]["USER"] != "campground_app":  # noqa: F405
    raise ImproperlyConfigured("Production runtime must use campground_app")
if not TRUSTED_PROXY_IPS:  # noqa: F405
    raise ImproperlyConfigured("Explicit trusted proxy addresses required")
