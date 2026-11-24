"""Strict file-only configuration. Error messages never include secret values."""

import os
import stat
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def read_secret(variable: str, minimum: int = 32) -> str:
    path = os.environ.get(variable)
    if not path:
        raise ImproperlyConfigured(f"Required secret file setting missing: {variable}")
    try:
        fd = os.open(Path(path), os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
                raise ValueError
            value = stream.read(4097).strip()
        if not minimum <= len(value) <= 4096 or len(set(value)) < 16:
            raise ValueError
        if any(
            marker in value.lower() for marker in ("changeme", "placeholder", "example", "insecure")
        ):
            raise ValueError
        return value
    except (OSError, ValueError):
        raise ImproperlyConfigured(f"Invalid or unreadable secret file: {variable}") from None
