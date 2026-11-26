import time

from allauth.account.authentication import get_authentication_records
from allauth.mfa.models import Authenticator
from django.core.exceptions import PermissionDenied


def client_ip(request):
    return getattr(request, "client_ip", request.META.get("REMOTE_ADDR", ""))


def axes_username(request, credentials=None):
    credentials = credentials or {}
    return (
        str(
            credentials.get("email") or credentials.get("username") or request.POST.get("login", "")
        )
        .strip()
        .casefold()
    )


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


def lock_staff(request, permission):
    """Recheck assurance and permissions while holding the account row lock.

    Call inside a transaction after locking the singleton campground policy.
    This prevents a stale request from mutating data after concurrent revocation.
    """
    from .middleware import security_stamp
    from .models import User

    if not request.user.is_authenticated:
        raise PermissionDenied
    request.user = User.objects.select_for_update().get(pk=request.user.pk)
    if request.session.get("security_stamp") != security_stamp(request.user):
        raise PermissionDenied("Your account security changed. Sign in again.")
    require_staff(request, permission)
    return request.user
