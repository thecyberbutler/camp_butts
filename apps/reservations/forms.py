from django import forms

from apps.campsites.models import Amenity, CampsiteType

from .services import date_range


class DatesForm(forms.Form):
    start = forms.DateField(label="Check-in", widget=forms.DateInput(attrs={"type": "date"}))
    end = forms.DateField(label="Check-out", widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        data = super().clean()
        if data.get("start") and data.get("end"):
            date_range(data["start"], data["end"])
        return data


class SearchForm(DatesForm):
    adults = forms.IntegerField(min_value=1, max_value=100, initial=1)
    site_type = forms.ModelChoiceField(CampsiteType.objects.all(), required=False)
    amenities = forms.ModelMultipleChoiceField(Amenity.objects.all(), required=False)
    rv_length = forms.IntegerField(min_value=0, max_value=100, initial=0)
    electric_amps = forms.TypedChoiceField(
        coerce=int, choices=[(0, "Any"), (30, "30 A"), (50, "50 A")]
    )
    pets = forms.BooleanField(required=False)


class BookingForm(DatesForm):
    submission_key = forms.UUIDField(widget=forms.HiddenInput)
    adults = forms.IntegerField(min_value=1, max_value=100, initial=1)
    children = forms.IntegerField(min_value=0, max_value=100, initial=0)
    pets = forms.IntegerField(min_value=0, max_value=20, initial=0)
    rv_length = forms.IntegerField(min_value=0, max_value=100, initial=0)
    notes = forms.CharField(max_length=2000, required=False, widget=forms.Textarea)


class CancelForm(forms.Form):
    reason = forms.CharField(max_length=500, required=False, widget=forms.Textarea)
    confirm = forms.BooleanField(label="I confirm cancellation of this reservation")
