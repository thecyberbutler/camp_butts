"""Generic HTML errors render without tenant, session or database dependencies."""

from django.http import HttpResponse
from django.template.loader import get_template

from config.environment import deployment_context

MESSAGES = {
    400: ("Invalid request", "The request could not be accepted."),
    403: ("Access denied", "You do not have access to this request."),
    404: ("Page not found", "The requested page is unavailable."),
    405: ("Method not allowed", "This request method is not supported."),
    413: ("Request too large", "The request exceeds the permitted size."),
    429: ("Too many requests", "Please wait before trying again."),
    500: ("Service unavailable", "The request could not be completed. Please try again later."),
}


def error_content(status):
    title, message = MESSAGES.get(status, MESSAGES[500])
    return get_template("error.html").render(
        {"error_title": title, "error_message": message, **deployment_context()}
    )


def bad_request(request, exception):
    return HttpResponse(error_content(400), status=400)


def permission_denied(request, exception):
    return HttpResponse(error_content(403), status=403)


def page_not_found(request, exception):
    return HttpResponse(error_content(404), status=404)


def server_error(request):
    return HttpResponse(error_content(500), status=500)
