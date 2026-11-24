bind = "0.0.0.0:8000"
workers = 3
threads = 1
timeout = 30
graceful_timeout = 30
limit_request_line = 4094
limit_request_fields = 50
limit_request_field_size = 4094
accesslog = None
forwarded_allow_ips = ""  # Django verifies the proxy peer itself.
umask = 0o077
worker_tmp_dir = "/run/gunicorn"
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {"safe": {"()": "config.logging.SafeFormatter"}},
    "handlers": {"safe": {"class": "logging.StreamHandler", "formatter": "safe"}},
    "root": {"handlers": ["safe"], "level": "WARNING"},
    "loggers": {
        "gunicorn.error": {"handlers": ["safe"], "level": "WARNING", "propagate": False},
        "gunicorn.access": {"handlers": ["safe"], "level": "WARNING", "propagate": False},
    },
}
