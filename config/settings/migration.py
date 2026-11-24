from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if DATABASES["default"]["USER"] != "campground_migrator":  # noqa: F405
    raise ImproperlyConfigured("Migrations require the separate migration role")
