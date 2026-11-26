import hashlib

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.http import HttpResponseForbidden
from django.utils import timezone

from apps.audit.services import record
from apps.configuration.models import Campground
from apps.notifications.models import Notification

from .models import Invitation
from .security import client_ip, privileged


class AccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        return super().clean_email(email).strip().casefold()

    def get_login_redirect_url(self, request):
        from django.urls import reverse

        return reverse("dashboard")

    def get_logout_redirect_url(self, request):
        from django.urls import reverse

        return reverse("home")

    def get_client_ip(self, request):
        return client_ip(request)

    def is_open_for_signup(self, request):
        return Campground.current().registration_mode != Campground.Registration.DISABLED

    def save_user(self, request, user, form, commit=True):
        try:
            with transaction.atomic():
                policy = Campground.current(lock=True)
                if policy.registration_mode == Campground.Registration.DISABLED:
                    raise ImmediateHttpResponse(
                        HttpResponseForbidden("Registration is unavailable.")
                    )
                if policy.registration_mode == Campground.Registration.INVITATION:
                    token = form.cleaned_data.get("invitation", "")
                    invite = (
                        Invitation.objects.select_for_update()
                        .filter(
                            digest=hashlib.sha256(token.encode()).hexdigest(),
                            enabled=True,
                            expires_at__gt=timezone.now(),
                        )
                        .first()
                    )
                    if not invite or invite.uses >= invite.max_uses:
                        raise ImmediateHttpResponse(
                            HttpResponseForbidden("Registration could not be completed.")
                        )
                    invite.uses += 1
                    invite.save(update_fields=["uses"])
                user = super().save_user(request, user, form, commit=False)
                user.email = user.email.casefold()
                user.phone = form.cleaned_data["phone"]
                user.is_staff = user.is_superuser = False
                user.approved = policy.registration_mode in {"open", "invitation"}
                user.policy_version = policy.policy_version
                user.policy_accepted_at = timezone.now()
                user.save()
                user.groups.add(Group.objects.get(name="Camper"))
                record(actor=user, action="account.registered", obj=user)
                Notification.objects.create(
                    recipient=user, message="Your account has been registered."
                )
                return user
        except IntegrityError:
            raise ImmediateHttpResponse(
                HttpResponseForbidden("Registration could not be completed.")
            ) from None


class MFAAdapter(DefaultMFAAdapter):
    def encrypt(self, text):
        return Fernet(settings.MFA_ENCRYPTION_KEY.encode()).encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text):
        return (
            Fernet(settings.MFA_ENCRYPTION_KEY.encode()).decrypt(encrypted_text.encode()).decode()
        )

    def can_delete_authenticator(self, authenticator):
        return not privileged(authenticator.user)
