import csv
import uuid
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import User
from apps.accounts.security import require_staff
from apps.audit.services import record
from apps.campsites.models import Campsite
from apps.configuration.models import Campground
from apps.notifications.models import Notification
from apps.reservations.forms import DatesForm
from apps.reservations.models import ACTIVE, Occupancy
from apps.reservations.services import BookingError, block, date_range, today, transition

from .forms import BlockForm, CampsiteForm, PolicyForm, TransitionForm


@login_required
def index(request):
    require_staff(request, "reservations.operate_reservations")
    local_today = today(Campground.current())
    active = Occupancy.objects.filter(status__in=ACTIVE)
    page = Paginator(Occupancy.objects.select_related("campsite", "camper"), 30).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "dashboard/operations.html",
        {
            "page_obj": page,
            "total_sites": Campsite.objects.filter(active=True).count(),
            "occupied": active.filter(dates__contains=local_today, kind="reservation").count(),
            "blocked": active.filter(dates__contains=local_today, kind="block").count(),
            "arrivals": active.filter(dates__startswith=local_today, kind="reservation").count(),
            "departures": active.filter(dates__endswith=local_today, kind="reservation").count(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def change_status(request, reservation_id):
    require_staff(request, "reservations.operate_reservations")
    item = get_object_or_404(Occupancy, pk=reservation_id, kind="reservation")
    form = TransitionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            transition(
                actor=request.user, reservation_id=item.pk, status=form.cleaned_data["status"]
            )
            return redirect("operations")
        except BookingError as error:
            form.add_error(None, error)
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": "Update reservation status", "submit": "Confirm status"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def maintenance(request):
    require_staff(request, "reservations.block_campsite")
    form = BlockForm(request.POST or None, initial={"submission_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        data["campsite_id"] = data.pop("campsite").pk
        try:
            block(actor=request.user, **data)
            return redirect("operations")
        except BookingError as error:
            form.add_error(None, error)
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": "Block a campsite", "submit": "Create maintenance block"},
    )


@login_required
def accounts(request):
    require_staff(request, "accounts.approve_camper")
    page = Paginator(
        User.objects.filter(approved=False, is_active=True).order_by("date_joined"), 30
    ).get_page(request.GET.get("page"))
    return render(request, "dashboard/accounts.html", {"page_obj": page})


@login_required
@require_POST
def approve(request, user_id):
    require_staff(request, "accounts.approve_camper")
    with transaction.atomic():
        Campground.current(lock=True)
        users = {
            u.pk: u
            for u in User.objects.select_for_update()
            .filter(pk__in=[request.user.pk, user_id])
            .order_by("pk")
        }
        actor = users[request.user.pk]
        if not actor.is_active or not actor.has_perm("accounts.approve_camper"):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        user = users.get(user_id)
        if user is None or not user.is_active or user.is_staff or user.is_superuser:
            from django.http import Http404

            raise Http404
        if not user.approved:
            user.approved = True
            user.security_version += 1
            user.save(update_fields=["approved", "security_version"])
            record(actor=actor, action="account.approved", obj=user)
            Notification.objects.create(
                recipient=user, message="Your campground account has been approved."
            )
    return redirect("account_approvals")


@login_required
@require_http_methods(["GET", "POST"])
def campsite_edit(request, site_id=None):
    require_staff(request, "campsites.change_campsite" if site_id else "campsites.add_campsite")
    with transaction.atomic():
        Campground.current(lock=True)
        item = (
            get_object_or_404(Campsite.objects.select_for_update(), pk=site_id) if site_id else None
        )
        form = CampsiteForm(request.POST or None, instance=item)
        if request.method == "POST" and form.is_valid():
            item = form.save()
            record(actor=request.user, action="campsite.updated", obj=item)
            return redirect("operations")
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": "Manage campsite", "submit": "Save campsite"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def configuration(request):
    require_staff(request, "configuration.change_campground")
    with transaction.atomic():
        policy = Campground.current(lock=True)
        form = PolicyForm(request.POST or None, instance=policy)
        if request.method == "POST" and form.is_valid():
            form.save()
            record(actor=request.user, action="configuration.updated", obj=policy)
            return redirect("operations")
    return render(
        request,
        "reservations/form.html",
        {"form": form, "title": "Campground policies", "submit": "Save policies"},
    )


@login_required
def calendar(request):
    require_staff(request, "reservations.operate_reservations")
    local_today = today(Campground.current())
    data = (
        request.GET
        if request.GET
        else {"start": local_today, "end": local_today + timedelta(days=7)}
    )
    form = DatesForm(data)
    rows, days = [], []
    if form.is_valid():
        start, end = form.cleaned_data["start"], form.cleaned_data["end"]
        if (end - start).days > 31:
            form.add_error(None, "Choose at most 31 days for the occupancy grid.")
        else:
            days = [start + timedelta(days=n) for n in range((end - start).days)]
            entries = list(
                Occupancy.objects.filter(status__in=ACTIVE, dates__overlap=date_range(start, end))
            )
            for site in Campsite.objects.all()[:100]:
                cells = [
                    next(
                        (
                            entry
                            for entry in entries
                            if entry.campsite_id == site.pk
                            and entry.check_in <= day < entry.check_out
                        ),
                        None,
                    )
                    for day in days
                ]
                rows.append((site, cells))
    return render(request, "dashboard/calendar.html", {"form": form, "rows": rows, "days": days})


def safe_csv(value):
    value = str(value)
    return (
        "'" + value
        if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))
        else value
    )


@login_required
def export(request):
    require_staff(request, "reservations.view_occupancy")
    form = DatesForm(request.GET)
    if not form.is_valid():
        return render(
            request, "dashboard/export.html", {"form": form}, status=400 if request.GET else 200
        )
    rows = Occupancy.objects.filter(
        dates__overlap=date_range(
            **{"start": form.cleaned_data["start"], "end": form.cleaned_data["end"]}
        )
    ).select_related("campsite")[:2000]
    with transaction.atomic():
        record(actor=request.user, action="report.exported", obj=Campground.current())
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="occupancy.csv"'
    writer = csv.writer(response)
    writer.writerow(["Campsite", "Check-in", "Check-out", "Kind", "Status"])
    for row in rows:
        writer.writerow(
            [safe_csv(row.campsite.name), row.check_in, row.check_out, row.kind, row.status]
        )
    return response
