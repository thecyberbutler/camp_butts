import time

from allauth.account.authentication import get_authentication_records
from allauth.mfa.models import Authenticator
from django.core.exceptions import PermissionDenied


def client_ip(request):
    return getattr(request, "client_ip", request.META.get("REMOTE_ADDR", ""))


def axes_username(request, credentials=None):
    return str((credentials or {}).get("username") or request.POST.get("login", "")).casefold()


def privileged(user):
    return user.is_authenticated and (
        user.is_staff or user.is_superuser or bool(user.get_all_permissions())
    )


def mfa_verified(request):
    if not request.user.is_authenticated:
        return False
    records = get_authentication_records(request, request.user)
    return Authenticator.objects.filter(user=request.user, type="totp").exists() and any(
        r.get("method") == "mfa" and 0 <= time.time() - r.get("at", 0) < 14400 for r in records
    )


def require_staff(request, permission):
    user = request.user
    if not (
        user.is_authenticated
        and user.is_active
        and user.approved
        and user.has_perm(permission)
        and mfa_verified(request)
    ):
        raise PermissionDenied
    if not any(
        0 <= time.time() - r.get("at", 0) <= 300 for r in get_authentication_records(request, user)
    ):
        raise PermissionDenied("Please reauthenticate before this operation.")
