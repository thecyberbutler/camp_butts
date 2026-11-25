import time

from allauth.account import signals as account_signals
from allauth.mfa import signals as mfa_signals
from allauth.socialaccount import signals as social_signals
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models import F
from django.dispatch import receiver

from apps.audit.models import Event
from apps.audit.services import record

from .middleware import security_stamp
from .models import User


@receiver(user_logged_in)
def session_started(sender, request, user, **kwargs):
    request.session["security_stamp"] = security_stamp(user)
    request.session["authenticated_at"] = time.time()
    request.session["last_activity"] = time.time()
    record(actor=user, action="auth.login", obj=user)


@receiver(user_logged_out)
def session_ended(sender, request, user, **kwargs):
    if user and user.is_authenticated:
        record(actor=user, action="auth.logout", obj=user)


@receiver(user_login_failed)
def login_failed(sender, credentials, request, **kwargs):
    Event.objects.create(action="auth.failed", object_type="accounts.user", outcome="denied")


def security_changed(sender, request, user, **kwargs):
    User.objects.filter(pk=user.pk).update(security_version=F("security_version") + 1)
    record(actor=user, action="account.security_changed", obj=user)
    # All current sessions become stale, including the current one. A fresh login
    # reestablishes both password and MFA assurance after changing security state.


for signal in (
    account_signals.password_changed,
    account_signals.password_reset,
    account_signals.email_changed,
    mfa_signals.authenticator_added,
    mfa_signals.authenticator_removed,
    mfa_signals.authenticator_reset,
):
    signal.connect(security_changed, weak=False)


@receiver(social_signals.social_account_added)
def google_connected(sender, request, sociallogin, **kwargs):
    security_changed(sender, request, sociallogin.user)


@receiver(social_signals.social_account_removed)
def google_disconnected(sender, request, socialaccount, **kwargs):
    security_changed(sender, request, socialaccount.user)
