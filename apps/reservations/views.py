import uuid

from allauth.core import ratelimit
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.campsites.models import Campsite

from . import services
from .forms import BookingForm, CancelForm, DatesForm


def limited(request):
    if not ratelimit.consume(request, action="reservation_write", key=str(request.user.pk)):
        return HttpResponse("Too many requests. Please try again later.", status=429)
    return None


@login_required
@require_http_methods(["GET", "POST"])
def book(request, site_id):
    services.eligible(request.user)
    site = get_object_or_404(Campsite, pk=site_id, active=True)
    form = BookingForm(
        request.POST or None,
        initial={
            "submission_key": uuid.uuid4(),
            "start": request.GET.get("start"),
            "end": request.GET.get("end"),
        },
    )
    if request.method == "POST":
        response = limited(request)
        if response is not None:
            return response
        if form.is_valid():
            try:
                item = services.book(actor=request.user, campsite_id=site.pk, **form.cleaned_data)
                return redirect("reservation_detail", reservation_id=item.pk)
            except services.BookingError as error:
                form.add_error(None, error)
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": f"Reserve {site.name}", "submit": "Create reservation"},
    )


@login_required
def detail(request, reservation_id):
    item = get_object_or_404(services.owned_query(request.user), pk=reservation_id)
    return render(request, "reservations/detail.html", {"reservation": item})


@login_required
@require_http_methods(["GET", "POST"])
def cancel(request, reservation_id):
    item = get_object_or_404(services.owned_query(request.user), pk=reservation_id)
    form = CancelForm(request.POST or None)
    if request.method == "POST":
        response = limited(request)
        if response is not None:
            return response
        if form.is_valid():
            try:
                services.cancel(
                    actor=request.user, reservation_id=item.pk, reason=form.cleaned_data["reason"]
                )
                messages.success(request, "Reservation cancelled.")
                return redirect("reservation_detail", reservation_id=item.pk)
            except services.BookingError as error:
                form.add_error(None, error)
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": "Cancel reservation", "submit": "Confirm cancellation"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def modify(request, reservation_id):
    item = get_object_or_404(services.owned_query(request.user), pk=reservation_id)
    form = DatesForm(request.POST or None, initial={"start": item.check_in, "end": item.check_out})
    if request.method == "POST":
        response = limited(request)
        if response is not None:
            return response
        if form.is_valid():
            try:
                services.modify(actor=request.user, reservation_id=item.pk, **form.cleaned_data)
                return redirect("reservation_detail", reservation_id=item.pk)
            except services.BookingError as error:
                form.add_error(None, error)
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": "Change reservation dates", "submit": "Save dates"},
    )
