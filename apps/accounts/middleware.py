import hashlib
import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .security import mfa_verified, privileged


def security_stamp(user):
    data = (
        user.approved,
        user.is_active,
        user.is_staff,
        user.is_superuser,
        user.security_version,
        sorted(user.get_all_permissions()),
    )
    return hashlib.sha256(repr(data).encode()).hexdigest()


class AccountSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        name = request.resolver_match.url_name
        if not settings.EMAIL_ENABLED and name in {
            "account_reset_password",
            "account_reset_password_done",
            "account_reset_password_from_key",
            "account_reset_password_from_key_done",
            "account_email",
            "account_confirm_email",
        }:
            return HttpResponseForbidden(
                "Email recovery and email changes require configured SMTP."
            )
        user = request.user
        if not user.is_authenticated:
            return None
        now = time.time()
        is_privileged = privileged(user)
        idle, absolute = (900, 14400) if is_privileged else (1800, 43200)
        stamp = security_stamp(user)
        if (
            request.session.get("security_stamp") != stamp
            or now - request.session.get("authenticated_at", 0) >= absolute
            or now - request.session.get("last_activity", 0) >= idle
        ):
            logout(request)
            return redirect("account_login")
        request.session["last_activity"] = now
        request.session.set_expiry(idle)
        # An unenrolled privileged user can only enroll MFA or sign out. No
        # prefix-based exemption lets alternate endpoints bypass this gate.
        enrollment = {
            "mfa_index",
            "mfa_activate_totp",
            "account_logout",
            "account_reauthenticate",
            "mfa_reauthenticate",
            "mfa_authenticate",
            "account_email_verification_sent",
        }
        if is_privileged and not mfa_verified(request) and name not in enrollment:
            return HttpResponseForbidden("Complete multi-factor authentication before continuing.")
        return None
