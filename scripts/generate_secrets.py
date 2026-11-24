"""Create fresh secret files without ever printing secret material."""

import argparse
import os
import secrets
from pathlib import Path


def generate(directory: Path) -> None:
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_mode & 0o077:
        raise SystemExit("Secret directory must be private (0700), not a symlink.")
    # 32 random bytes in urlsafe base64 is a Fernet key; no custom cryptography.
    import base64

    values = {
        "django_key": secrets.token_urlsafe(64),
        "mfa_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "session_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "database_password": secrets.token_urlsafe(48),
        "migration_password": secrets.token_urlsafe(48),
        "admin_password": secrets.token_urlsafe(48),
    }
    if any((directory / name).exists() for name in values):
        raise SystemExit("Refusing to overwrite existing secrets.")
    for name, value in values.items():
        fd = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(value)
    print("Created protected secret files; values are not displayed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    generate(parser.parse_args().directory)
