import re

from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.template.loader import get_template

from .context import directory, lookup, tenant_scope


class TenantMiddleware:
    """Resolve the URL before authentication, and keep response/session writes scoped."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith(settings.STATIC_URL):
            return self.get_response(request)
        selected = request.GET.getlist("campground")
        if request.path_info == "/":
            if request.method not in ("GET", "HEAD"):
                return HttpResponseBadRequest("Select a campground first.")
            if selected:
                if (
                    len(selected) != 1
                    or len(selected[0]) > 63
                    or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", selected[0])
                ):
                    return HttpResponseBadRequest("Invalid campground selector.")
                tenant = lookup(selected[0])
                if tenant is None:
                    return HttpResponseNotFound("Campground not found.")
                return HttpResponseRedirect(f"/c/{tenant.slug}/")
            return HttpResponse(
                get_template("tenancy/directory.html").render({"campgrounds": directory()})
            )
        match = re.match(r"^/c/([a-z0-9]+(?:-[a-z0-9]+)*)/", request.path_info)
        if not match or len(match[1]) > 63:
            return HttpResponseNotFound("Select a campground.")
        tenant = lookup(match[1])
        if tenant is None:
            return HttpResponseNotFound("Campground not found.")
        if selected and (len(selected) != 1 or selected[0] != tenant.slug):
            return HttpResponseBadRequest("Conflicting campground selectors.")
        request.tenant = tenant
        request.path_info = "/" + request.path_info[match.end() :]
        request.META["SCRIPT_NAME"] = f"/c/{tenant.slug}"
        request.META["PATH_INFO"] = request.path_info
        with tenant_scope(tenant, urls=True):
            response = self.get_response(request)
            # Exceptions converted to responses by Django must not commit partial writes.
            if response.status_code >= 500:
                from django.db import transaction

                transaction.set_rollback(True)
            return response
