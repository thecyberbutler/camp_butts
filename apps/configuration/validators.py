from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def public_https_url(value):
    if not value:
        return
    URLValidator(schemes=["https"])(value)
    parsed = urlsplit(value)
    if parsed.username is not None or parsed.password is not None:
        raise ValidationError("Website links must not include credentials.")
