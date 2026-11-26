import copy

from allauth.core import ratelimit
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView, OAuth2LoginView
from allauth.socialaccount.views import ConnectionsView, SignupView
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import SignupForm as LocalSignupForm
from apps.accounts.models import User
from apps.configuration.models import Campground

from .adapter import require_link_assurance, valid_state
from .provider import VerifiedGoogleOAuth2Adapter


def enabled(request):
    if request.tenant.slug not in settings.GOOGLE_OAUTH_APPS:
        raise Http404


@require_http_methods(["GET", "POST"])
def google_login(request):
    enabled(request)
    if not ratelimit.consume(request, action="google_start"):
        return HttpResponse(status=429)
    response = OAuth2LoginView.adapter_view(VerifiedGoogleOAuth2Adapter)(request)
    if request.method == "POST" and response.status_code == 302:
        # Navigate from a complete same-origin document. Some browsers apply
        # form-action to redirect chains; do not relax CSP to accommodate them.
        return render(request, "google_auth/redirect.html", {"google_url": response["Location"]})
    return response


class GoogleCallbackView(OAuth2CallbackView):
    def _get_state(self, request, provider):
        # TenantMiddleware holds the outer transaction. Lock/reload the encrypted session
        # before consuming state so simultaneous callbacks cannot both consume it.
        session_key = request.session.session_key
        if session_key:
            Session.objects.select_for_update().filter(session_key=session_key).first()
            request.session.__dict__.pop("_session_cache", None)
        state, response = super()._get_state(request, provider)
        if response:
            return state, response
        if not valid_state(state) or state.get("client_id") != provider.app.client_id:
            raise PermissionDenied
        request.google_oauth_state = state
        return state, None


@require_http_methods(["GET"])
def google_callback(request):
    enabled(request)
    if not ratelimit.consume(request, action="google_callback"):
        return HttpResponse(status=429)
    # Duplicate callback inputs are ambiguous and must not reach the provider.
    if any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        raise PermissionDenied
    try:
        return GoogleCallbackView.adapter_view(VerifiedGoogleOAuth2Adapter)(request)
    except IntegrityError:
        # Concurrent links/identity uniqueness never leak database diagnostics.
        raise PermissionDenied from None


class GoogleSignupForm(SocialSignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (
            "first_name",
            "last_name",
            "phone",
            "rules_agreed",
            "policies_agreed",
            "invitation",
        ):
            self.fields[name] = copy.deepcopy(LocalSignupForm.base_fields[name])
        self.fields["email"].disabled = True
        self.fields["phone"].help_text = (
            "Optional. Review the number suggested by Google, or enter a contact number. "
            "This does not verify the number or enable phone sign-in."
        )
        for name in ("first_name", "last_name"):
            self.fields[name].help_text = "Review the name suggested by Google or enter your name."


class GoogleSignupView(SignupView):
    def dispatch(self, request, *args, **kwargs):
        enabled(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not ratelimit.consume(self.request, action="signup"):
            return HttpResponse(status=429)
        # Preserve the existing uniform registration result and no automatic sign-in.
        if not form.account_already_exists:
            try:
                with transaction.atomic():
                    user = form.save(self.request)
                if settings.EMAIL_ENABLED:
                    from allauth.account.models import EmailAddress

                    email = EmailAddress.objects.get(user=user, primary=True)
                    if not email.verified:
                        email.send_confirmation(self.request, signup=True)
            except ImmediateHttpResponse:
                pass
        self.request.session.pop("socialaccount_sociallogin", None)
        return redirect("registration_received")


class GoogleConnectionsView(ConnectionsView):
    def dispatch(self, request, *args, **kwargs):
        enabled(request)
        if request.method == "POST":
            Campground.current(lock=True)
            if not request.user.is_authenticated:
                raise PermissionDenied
            request.user = User.objects.select_for_update().get(pk=request.user.pk)
            require_link_assurance(request)
            # Lock links with the same policy/account order used by connecting.
            list(SocialAccount.objects.select_for_update().filter(user=request.user))
        return super().dispatch(request, *args, **kwargs)
