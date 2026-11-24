from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def index(request):
    page = Paginator(Notification.objects.filter(recipient=request.user), 30).get_page(
        request.GET.get("page")
    )
    return render(request, "notifications/index.html", {"page_obj": page})


@login_required
@require_POST
def mark_read(request, notification_id):
    item = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    if item.read_at is None:
        item.read_at = timezone.now()
        item.save(update_fields=["read_at"])
    return redirect("notifications")
