"""Encrypt a bounded database dump from a pipe; never persist or display plaintext."""

import os
import sys
from pathlib import Path

from cryptography.fernet import Fernet


def encrypt_snapshot(source, key_directory: Path, output_directory: Path):
    for directory in (key_directory, output_directory):
        info = directory.lstat()
        if directory.is_symlink() or not directory.is_dir() or info.st_mode & 0o077:
            raise ValueError("Protected snapshot directories required")
    data = source.read(64 * 1024 * 1024 + 1)
    if not data.startswith(b"PGDMP") or len(data) > 64 * 1024 * 1024:
        raise ValueError("Invalid or oversized database snapshot")
    key = Fernet.generate_key()
    with os.fdopen(
        os.open(key_directory / "snapshot.key", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
    ) as stream:
        stream.write(key)
        stream.flush()
        os.fsync(stream.fileno())
    cipher = Fernet(key)
    with os.fdopen(
        os.open(
            output_directory / "database.dump.fernet", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        ),
        "wb",
    ) as stream:
        stream.write(cipher.encrypt(data))
        stream.flush()
        os.fsync(stream.fileno())
    if cipher.decrypt((output_directory / "database.dump.fernet").read_bytes()) != data:
        raise ValueError("Encrypted snapshot verification failed")


if __name__ == "__main__":
    try:
        encrypt_snapshot(sys.stdin.buffer, Path("/recovery-key"), Path("/snapshot"))
        print("Database snapshot encrypted and authenticated decryption verified.")
    except Exception:
        raise SystemExit("Snapshot creation failed; sensitive diagnostics withheld.") from None
