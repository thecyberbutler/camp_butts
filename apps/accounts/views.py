from allauth.account.models import EmailAddress
from allauth.account.views import SignupView as AllauthSignupView
from allauth.core.exceptions import ImmediateHttpResponse
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.shortcuts import redirect, render


class SignupView(AllauthSignupView):
    def form_valid(self, form):
        # Same response and no automatic login for existing/new identities.
        # Hashing on the duplicate branch reduces the obvious timing oracle.
        if form.account_already_exists:
            make_password(form.cleaned_data["password1"])
        else:
            try:
                with transaction.atomic():
                    user = form.save(self.request)
                if settings.EMAIL_ENABLED:
                    EmailAddress.objects.get(user=user, primary=True).send_confirmation(
                        self.request, signup=True
                    )
            except ImmediateHttpResponse:
                pass  # Expected invalid invitation or identity conflict; generic result.
        return redirect("registration_received")


def registration_received(request):
    return render(request, "accounts/registration_received.html")
