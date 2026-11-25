from io import BytesIO

import pytest
from cryptography.fernet import Fernet, InvalidToken

from scripts.encrypt_deployment_snapshot import encrypt_snapshot


def test_snapshot_encrypts_authenticates_and_refuses_overwrites(tmp_path):
    key = tmp_path / "key"
    output = tmp_path / "backup"
    key.mkdir(mode=0o700)
    output.mkdir(mode=0o700)
    plaintext = b"PGDMP" + b"synthetic-private-database-data" * 100
    encrypt_snapshot(BytesIO(plaintext), key, output)
    ciphertext = (output / "database.dump.fernet").read_bytes()
    cipher = Fernet((key / "snapshot.key").read_bytes())
    assert plaintext not in ciphertext and cipher.decrypt(ciphertext) == plaintext
    assert (key / "snapshot.key").stat().st_mode & 0o777 == 0o600
    assert (output / "database.dump.fernet").stat().st_mode & 0o777 == 0o600
    with pytest.raises(InvalidToken):
        cipher.decrypt(ciphertext[:-10] + b"tampered!!")
    with pytest.raises(FileExistsError):
        encrypt_snapshot(BytesIO(plaintext), key, output)
    assert (output / "database.dump.fernet").read_bytes() == ciphertext


def test_snapshot_refuses_plaintext_or_unprotected_destination(tmp_path):
    key = tmp_path / "key"
    key.mkdir(mode=0o700)
    output = tmp_path / "backup"
    output.mkdir(mode=0o755)
    output.chmod(0o755)  # Make the negative case independent of the caller's secure umask.
    with pytest.raises(ValueError):
        encrypt_snapshot(BytesIO(b"PGDMPsynthetic"), key, output)
    output.chmod(0o700)
    with pytest.raises(ValueError):
        encrypt_snapshot(BytesIO(b"not-a-database-archive"), key, output)
    assert not list(key.iterdir()) and not list(output.iterdir())
