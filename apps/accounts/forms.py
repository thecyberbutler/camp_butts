from allauth.account.adapter import get_adapter
from allauth.account.forms import SignupForm as AllauthSignupForm
from django import forms


class SignupForm(AllauthSignupForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    phone = forms.RegexField(r"^[0-9+() .-]{0,32}$", max_length=32, required=False)
    rules_agreed = forms.BooleanField(label="I agree to the campground rules")
    policies_agreed = forms.BooleanField(label="I agree to the reservation policies")
    invitation = forms.CharField(max_length=100, required=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].max_length = 256
        self.fields["password2"].max_length = 256

    def clean_username(self):
        # Validate syntax without disclosing whether this identity exists.
        return get_adapter().clean_username(self.cleaned_data["username"], shallow=True).casefold()
