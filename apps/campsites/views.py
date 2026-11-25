from allauth.core import ratelimit
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.configuration.models import Campground
from apps.notifications.models import Notification
from apps.reservations.forms import DatesForm, SearchForm
from apps.reservations.models import ACTIVE, Occupancy
from apps.reservations.services import available, date_range, owned_query

from .models import Campsite


def home(request):
    return render(request, "home.html")


def campground_map(request):
    policy = Campground.current()
    if not policy.public_availability and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(request.path)
    if not ratelimit.consume(request, action="availability"):
        return HttpResponse("Too many requests. Please try again later.", status=429)
    form = DatesForm(request.GET or None)
    sites = list(Campsite.objects.all()[:100]) if policy.booking_enabled else []
    entries = []
    if form.is_valid():
        entries = list(
            Occupancy.objects.filter(
                status__in=ACTIVE, dates__overlap=date_range(**form.cleaned_data)
            ).values("campsite_id", "kind")
        )
    for site in sites:
        site.map_status = "unavailable"
        if site.active and form.is_valid():
            site.map_status = "available"
            for item in entries:
                if item["campsite_id"] == site.pk:
                    site.map_status = "maintenance" if item["kind"] == "block" else "reserved"
    return render(request, "campsites/map.html", {"sites": sites, "form": form})


def listing(request):
    policy = Campground.current()
    show_availability = policy.public_availability or request.user.is_authenticated
    form = SearchForm(request.GET or None)
    sites = Campsite.objects.filter(active=True).select_related("site_type")
    if request.GET and show_availability:
        if not ratelimit.consume(request, action="availability"):
            return HttpResponse("Too many requests. Please try again later.", status=429)
        sites = available(**form.cleaned_data) if form.is_valid() else sites.none()
    page = Paginator(sites, 24).get_page(request.GET.get("page"))
    template = (
        "campsites/results.html"
        if request.headers.get("HX-Request") == "true"
        else "campsites/list.html"
    )
    return render(
        request, template, {"page_obj": page, "form": form, "show_availability": show_availability}
    )


def detail(request, site_id):
    return render(
        request,
        "campsites/detail.html",
        {
            "site": get_object_or_404(
                Campsite.objects.select_related("site_type").prefetch_related("amenities"),
                pk=site_id,
                active=True,
            )
        },
    )


@login_required
def dashboard(request):
    page = Paginator(owned_query(request.user), 20).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard.html",
        {
            "page_obj": page,
            "notifications": Notification.objects.filter(recipient=request.user)[:5],
        },
    )
