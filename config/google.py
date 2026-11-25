"""Optional per-campground OAuth credentials, supplied only through a protected file."""

import json
import os
import re

from django.core.exceptions import ImproperlyConfigured

from config.secrets import read_secret


def google_configuration():
    if not os.environ.get("GOOGLE_OAUTH_CONFIG_FILE"):
        return {}
    try:

        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError
                result[key] = value
            return result

        config = json.loads(
            read_secret("GOOGLE_OAUTH_CONFIG_FILE", 64), object_pairs_hook=unique_object
        )
        if not isinstance(config, dict) or not config:
            raise ValueError
        for slug, app in config.items():
            if len(slug) > 63 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                raise ValueError
            if not isinstance(app, dict) or set(app) != {"client_id", "secret"}:
                raise ValueError
            if not isinstance(app["client_id"], str) or not re.fullmatch(
                r"[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com", app["client_id"]
            ):
                raise ValueError
            secret = app["secret"]
            if (
                not isinstance(secret, str)
                or not 24 <= len(secret) <= 256
                or len(set(secret)) < 12
                or any(c.isspace() for c in secret)
            ):
                raise ValueError
        return config
    except (ValueError, TypeError, AttributeError):
        raise ImproperlyConfigured("Invalid protected Google OAuth configuration") from None
