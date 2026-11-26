"""Allauth authorization-code flow with PKCE, tenant-bound state and verified OIDC claims."""

import secrets
import time

import jwt
from allauth.account.models import EmailAddress
from allauth.socialaccount.internal import jwtkit
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from apps.accounts.middleware import security_stamp
from apps.tenancy.context import current_tenant

from .adapter import require_link_assurance
from .constants import GOOGLE_SCOPES, PHONE_SCOPE
from .profile import profile_name, profile_phone


class VerifiedGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        # Use established JWT verification with a fixed algorithm and required claims.
        # No userinfo fallback, unsigned token acceptance or browser-token endpoint.
        try:
            credential = kwargs["response"]["id_token"]
            if not isinstance(credential, str) or len(credential) > 16384:
                raise ValueError
            if jwt.get_unverified_header(credential).get("alg") != "RS256":
                raise ValueError
            _, key = jwtkit.fetch_key(
                credential,
                "https://www.googleapis.com/oauth2/v1/certs",
                jwtkit.lookup_kid_pem_x509_certificate,
            )
            claims = jwt.decode(
                credential,
                key,
                algorithms=["RS256"],
                audience=app.client_id,
                issuer=["https://accounts.google.com", "accounts.google.com"],
                options={"require": ["iss", "aud", "exp", "iat", "sub", "nonce"]},
            )
            state = request.google_oauth_state
            if (
                claims.get("azp", app.client_id) != app.client_id
                or not isinstance(claims["nonce"], str)
                or not secrets.compare_digest(claims["nonce"], state["nonce"])
                or claims.get("email_verified") is not True
                or not isinstance(claims["sub"], str)
                or not 1 <= len(claims["sub"]) <= 191
            ):
                raise ValueError
            claims["email"] = forms.EmailField().clean(claims.get("email", "")).casefold()
            sociallogin = self.get_provider().sociallogin_from_response(request, claims)
            granted = kwargs["response"].get("scope")
            phone_granted = granted is None or (
                isinstance(granted, str) and PHONE_SCOPE in granted.split()
            )
            if (
                state.get("process") == "login"
                and phone_granted
                and not SocialAccount.objects.filter(provider="google", uid=claims["sub"]).exists()
            ):
                sociallogin.user.phone = profile_phone(token.token)
            return sociallogin
        except (KeyError, ValueError, TypeError, AttributeError, ValidationError, jwt.PyJWTError):
            raise OAuth2Error("Google identity verification failed") from None


class SecureGoogleProvider(GoogleProvider):
    oauth2_adapter_class = VerifiedGoogleOAuth2Adapter
    supports_token_authentication = False

    def get_scope_from_request(self, request):
        return list(GOOGLE_SCOPES)

    def get_auth_params_from_request(self, request, action):
        return {"access_type": "online", "prompt": "select_account"}

    def get_pkce_params(self):
        from allauth.socialaccount.providers.oauth2.utils import generate_code_challenge

        return generate_code_challenge()

    def redirect(self, request, process, next_url=None, data=None, **kwargs):
        if process not in {"login", "connect"}:
            raise PermissionDenied
        if process == "connect":
            require_link_assurance(request)
        elif request.user.is_authenticated:
            raise PermissionDenied
        nonce = secrets.token_urlsafe(32)
        return super().redirect(
            request,
            process,
            next_url=reverse("socialaccount_connections" if process == "connect" else "dashboard"),
            auth_params={"access_type": "online", "prompt": "select_account", "nonce": nonce},
            scope=list(GOOGLE_SCOPES),
            nonce=nonce,
            tenant=str(current_tenant().id),
            client_id=self.app.client_id,
            created_at=time.time(),
            actor=str(request.user.pk) if process == "connect" else None,
            stamp=security_stamp(request.user) if process == "connect" else None,
        )

    def extract_common_fields(self, data):
        return {
            "email": data["email"],
            "first_name": profile_name(data.get("given_name")),
            "last_name": profile_name(data.get("family_name")),
        }

    def extract_extra_data(self, data):
        return {"email": data["email"]}

    def extract_email_addresses(self, data):
        # Google does not attest current ownership of arbitrary third-party mailboxes.
        authoritative = data["email"].endswith("@gmail.com") or bool(data.get("hd"))
        return [EmailAddress(email=data["email"], verified=authoritative, primary=True)]

    def verify_token(self, request, token):
        raise PermissionDenied


provider_classes = [SecureGoogleProvider]
