import os
from datetime import timedelta
from pathlib import Path

from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured

from config.environment import validate_environment
from config.secrets import read_secret

BASE_DIR = Path(__file__).resolve().parents[2]
DEBUG = False
APP_ENVIRONMENT = validate_environment(os.environ.get("APP_ENVIRONMENT", "production"))
SECRET_KEY = read_secret("DJANGO_SECRET_KEY_FILE", 64)
MFA_ENCRYPTION_KEY = read_secret("MFA_KEY_FILE", 44)
SESSION_ENCRYPTION_KEY = read_secret("SESSION_KEY_FILE", 44)
try:
    Fernet(MFA_ENCRYPTION_KEY.encode())
    Fernet(SESSION_ENCRYPTION_KEY.encode())
except (ValueError, TypeError):
    raise ImproperlyConfigured("Invalid MFA key file") from None
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
if not all(ALLOWED_HOSTS) or any("*" in h or "/" in h or ":" in h for h in ALLOWED_HOSTS):
    raise ImproperlyConfigured("Explicit DNS allowed hosts required")
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
INSTALLED_APPS = [
    "apps.tenancy.apps.TenancyConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "allauth",
    "allauth.account",
    "allauth.mfa",
    "allauth.usersessions",
    "axes",
    "apps.accounts.apps.AccountsConfig",
    "apps.configuration",
    "apps.campsites",
    "apps.reservations",
    "apps.notifications",
    "apps.audit",
]
MIDDLEWARE = [
    "config.middleware.ProxyBoundaryMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "config.middleware.ResponseSecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "apps.tenancy.middleware.TenantMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "allauth.usersessions.middleware.UserSessionsMiddleware",
    "apps.accounts.middleware.AccountSecurityMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.configuration.context.campground",
                "config.environment.deployment_context",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "campground"),
        "USER": os.environ.get("DATABASE_USER", "campground_app"),
        "PASSWORD": read_secret("DATABASE_PASSWORD_FILE"),
        "HOST": os.environ.get("DATABASE_HOST", "db"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "options": "-c statement_timeout=10000 -c lock_timeout=5000 -c search_path=pg_catalog"
        },
    }
}
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 15},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "apps.accounts.validators.MaximumPasswordLengthValidator"},
]
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "dashboard"
ALLAUTH_SETTING_GETTER = "apps.tenancy.allauth.setting"
# Bandit B105 reviewed: this is allauth's import path, never a password/token value.
ACCOUNT_PASSWORD_RESET_TOKEN_GENERATOR = "apps.accounts.tokens.TenantPasswordResetTokenGenerator"  # nosec B105
ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"
ACCOUNT_FORMS = {"signup": "apps.accounts.forms.SignupForm"}
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_PREVENT_ENUMERATION = "strict"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = False
ACCOUNT_REAUTHENTICATION_REQUIRED = True
ACCOUNT_REAUTHENTICATION_TIMEOUT = 300
ACCOUNT_LOGIN_TIMEOUT = 300
ACCOUNT_EMAIL_VERIFICATION = "mandatory" if os.environ.get("EMAIL_ENABLED") == "true" else "none"
ACCOUNT_EMAIL_NOTIFICATIONS = False
RECOVERY_RATE = "3/h/ip,3/h/key"
ACCOUNT_RATE_LIMITS = {
    "login": "10/m/ip",
    "login_failed": "5/5m/key,20/5m/ip",
    "signup": "5/h/ip",
    "reservation_write": "20/m/key,40/m/ip",
    "availability": "60/m/ip",
    "reset_password": RECOVERY_RATE,
}
MFA_ADAPTER = "apps.accounts.adapters.MFAAdapter"
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]
MFA_TOTP_ISSUER = "Campground"
MFA_ALLOW_UNVERIFIED_EMAIL = False
USERSESSIONS_TRACK_ACTIVITY = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_USERNAME_CALLABLE = "apps.accounts.security.axes_username"
AXES_CLIENT_IP_CALLABLE = "apps.accounts.security.client_ip"
AXES_SENSITIVE_PARAMETERS = ["username", "ip_address"]
AXES_VERBOSE = False
AXES_RESET_ON_SUCCESS = False
AXES_ENABLE_ACCESS_FAILURE_LOG = False
AXES_ENABLE_ACCESS_SUCCESS_LOG = False
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "security_cache",
        "KEY_FUNCTION": "config.cache.private_cache_key",
    }
}
SESSION_ENGINE = "config.sessions"
SESSION_COOKIE_NAME = "__Host-sessionid"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_NAME = "__Host-csrftoken"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = False
TRUSTED_PROXY_IPS = set(os.environ.get("TRUSTED_PROXY_IPS", "").split(",")) - {""}
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 65536
DATA_UPLOAD_MAX_NUMBER_FIELDS = 40
DATA_UPLOAD_MAX_NUMBER_FILES = 0
FILE_UPLOAD_MAX_MEMORY_SIZE = 0
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = os.environ.get("APP_TIME_ZONE", "America/New_York")
LANGUAGE_CODE = "en-us"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Only the deployment-collected, read-only asset directory is served. No media,
# automatic filesystem refresh, source finders or cross-origin wildcard access.
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = False
WHITENOISE_ALLOW_ALL_ORIGINS = False
WHITENOISE_ROOT = None
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED") == "true"
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_ENABLED
    else "apps.accounts.email.DisabledEmailBackend"
)
if EMAIL_ENABLED:
    EMAIL_HOST = os.environ["EMAIL_HOST"]
    EMAIL_PORT = 587
    EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
    EMAIL_HOST_PASSWORD = read_secret("EMAIL_PASSWORD_FILE")
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 10
    DEFAULT_FROM_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]
PASSWORD_RESET_TIMEOUT = 900
# Formatters retain event categories only, never arbitrary messages, URLs or exceptions.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {"safe": {"()": "config.logging.SafeFormatter"}},
    "handlers": {"safe": {"class": "logging.StreamHandler", "formatter": "safe"}},
    "root": {"handlers": ["safe"], "level": "WARNING"},
}
