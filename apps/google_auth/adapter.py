import secrets
import time

from allauth.account.authentication import get_authentication_records
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseForbidden

from apps.accounts.middleware import security_stamp
from apps.accounts.models import User
from apps.accounts.security import mfa_verified, privileged
from apps.configuration.models import Campground
from apps.tenancy.context import current_tenant

from .transport import GoogleSession


def valid_state(state):
    return (
        isinstance(state, dict)
        and state.get("tenant") == str(current_tenant().id)
        and 0 <= time.time() - state.get("created_at", 0) < 300
    )


def require_link_assurance(request):
    user = request.user
    if not (
        user.is_authenticated
        and user.is_active
        and user.approved
        and request.session.get("security_stamp") == security_stamp(user)
        and any(
            r.get("method") == "password" and 0 <= time.time() - r.get("at", 0) < 300
            for r in get_authentication_records(request, user)
        )
        and (not privileged(user) or mfa_verified(request))
    ):
        raise PermissionDenied("Sign in with your password again before changing Google access.")


class GoogleAccountAdapter(DefaultSocialAccountAdapter):
    def list_apps(self, request, provider=None, client_id=None):
        tenant = getattr(request, "tenant", None)
        app = settings.GOOGLE_OAUTH_APPS.get(tenant.slug) if tenant else None
        if not app or provider not in (None, "google"):
            return []
        if client_id is not None and client_id != app["client_id"]:
            return []
        return [SocialApp(provider="google", name="Google", **app)]

    def get_requests_session(self):
        return GoogleSession()

    def get_signup_form_initial_data(self, sociallogin):
        initial = super().get_signup_form_initial_data(sociallogin)
        initial["phone"] = sociallogin.user.phone or ""
        return initial

    def generate_state_param(self, state):
        return secrets.token_urlsafe(32)

    def can_authenticate_by_email(self, login, email):
        return False

    def pre_social_login(self, request, sociallogin):
        # Neither a token nor the raw ID-token claims may enter pending signup storage.
        sociallogin.token = None
        if not valid_state(sociallogin.state):
            raise PermissionDenied
        if sociallogin.state.get("process") == "connect":
            Campground.current(lock=True)
            request.user = User.objects.select_for_update().get(pk=request.user.pk)
            require_link_assurance(request)
            if (
                sociallogin.state.get("actor") != str(request.user.pk)
                or sociallogin.state.get("stamp") != security_stamp(request.user)
                or sociallogin.account.extra_data.get("email", "").casefold()
                != request.user.email.casefold()
            ):
                raise PermissionDenied
        elif sociallogin.is_existing:
            from axes.handlers.proxy import AxesProxyHandler

            if (
                not sociallogin.user.is_active
                or not sociallogin.user.approved
                or not AxesProxyHandler.is_allowed(request, {"email": sociallogin.user.email})
            ):
                raise ImmediateHttpResponse(
                    HttpResponseForbidden("Sign-in could not be completed.")
                )

    def is_open_for_signup(self, request, sociallogin):
        return valid_state(sociallogin.state) and super().is_open_for_signup(request, sociallogin)

    def save_user(self, request, sociallogin, form=None):
        if form is None or not self.is_open_for_signup(request, sociallogin):
            raise PermissionDenied
        with transaction.atomic():
            return super().save_user(request, sociallogin, form)

    def validate_disconnect(self, account, accounts):
        from allauth.core import context

        require_link_assurance(context.request)

    def on_authentication_error(self, request, provider, **kwargs):
        # Never render callback query parameters, OAuth state or provider exceptions.
        from apps.audit.models import Event

        Event.objects.create(action="auth.google_failed", outcome="denied")
        raise ImmediateHttpResponse(HttpResponseForbidden("Google sign-in could not be completed."))
