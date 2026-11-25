from django import forms

from apps.campsites.models import Amenity, Campsite, CampsiteType
from apps.configuration.models import Campground
from apps.reservations.forms import DatesForm


class BlockForm(DatesForm):
    campsite = forms.ModelChoiceField(Campsite.objects.all())
    reason = forms.CharField(max_length=500)
    submission_key = forms.UUIDField(widget=forms.HiddenInput)


class TransitionForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (v, v.replace("_", " ").title())
            for v in ("confirmed", "rejected", "cancelled", "checked_in", "checked_out", "no_show")
        ]
    )


class AccountStateForm(forms.Form):
    active = forms.TypedChoiceField(
        choices=[("false", "Deactivate account"), ("true", "Reactivate account")],
        coerce=lambda value: value == "true",
    )
    confirm = forms.BooleanField(label="I confirm this account status change")


class CampsiteTypeForm(forms.ModelForm):
    class Meta:
        model = CampsiteType
        fields = ["name"]


class AmenityForm(forms.ModelForm):
    class Meta:
        model = Amenity
        fields = ["name"]


class CampsiteForm(forms.ModelForm):
    class Meta:
        model = Campsite
        fields = [
            "name",
            "description",
            "site_type",
            "amenities",
            "active",
            "max_occupancy",
            "max_rv_length",
            "pull_through",
            "electric_amps",
            "water",
            "sewer",
            "wifi",
            "pets_allowed",
            "accessibility",
            "map_x",
            "map_y",
            "display_order",
        ]


class PolicyForm(forms.ModelForm):
    website_url = forms.URLField(required=False, max_length=500, assume_scheme="https")
    map_url = forms.URLField(required=False, max_length=500, assume_scheme="https")

    class Meta:
        model = Campground
        fields = [
            "name",
            "welcome",
            "address",
            "contact_phone",
            "website_url",
            "map_url",
            "rate_information",
            "rules",
            "reservation_policy",
            "policy_version",
            "timezone",
            "min_nights",
            "max_nights",
            "max_active",
            "advance_days",
            "notice_days",
            "cancellation_days",
            "modification_days",
            "allow_cancel",
            "allow_modify",
            "multiple_sites",
            "approval_required",
            "pending_hours",
        ]
        # Registration and public visibility changes use an explicit operator
        # workflow, not an incidental business-policy form.
