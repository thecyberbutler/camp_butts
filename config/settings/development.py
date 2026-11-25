from .base import *  # noqa: F403

# Development retains TLS, secure cookies, Argon2, MFA and rate limits.

# This label cannot be suppressed by a production-valued environment variable.
APP_ENVIRONMENT = "development"
