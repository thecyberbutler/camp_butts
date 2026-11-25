import os
import secrets
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet

# Disposable keys; no production secret is read. Test requests still enforce HTTPS,
# secure cookies, password hashing, MFA and rate limits.
_secret_dir = tempfile.TemporaryDirectory(prefix="campground-test-")
for _name, _value in {
    "DJANGO_SECRET_KEY_FILE": secrets.token_urlsafe(64),
    "MFA_KEY_FILE": Fernet.generate_key().decode(),
    "SESSION_KEY_FILE": Fernet.generate_key().decode(),
}.items():
    _path = Path(_secret_dir.name) / _name
    _path.touch(mode=0o600)
    _path.write_text(_value)
    os.environ[_name] = str(_path)
os.environ["DJANGO_ALLOWED_HOSTS"] = "testserver,localhost"
os.environ["EMAIL_ENABLED"] = "false"
from .base import *  # noqa: E402,F403

if not DATABASES["default"]["NAME"].startswith("campground_test"):  # noqa: F405
    raise RuntimeError("Tests require a dedicated campground_test database")

# Django creates the disposable test schema before tenant policies are installed.
DATABASES["default"]["OPTIONS"]["options"] += (  # noqa: F405
    " -c search_path=public,campground_extensions,pg_catalog"
)

DATABASES["default"]["TEST"] = {"TEMPLATE": "campground_test_template"}  # noqa: F405

# This label cannot be suppressed by a production-valued environment variable.
APP_ENVIRONMENT = "test"
