"""Tenant context through allauth's supported settings hook, never mutable globals."""

from django.conf import settings

from .context import current_tenant


def setting(name, default):
    value = getattr(settings, name, default)
    if name == "ACCOUNT_SALT":
        # allauth's signed email confirmation otherwise contains only a schema-local ID.
        return f"{value}:{current_tenant().id}"
    if name == "MFA_TOTP_ISSUER":
        return f"{value} ({current_tenant().slug})"
    return value
