from ipaddress import ip_address

from django.conf import settings

from config.errors import bad_request


class ProxyBoundaryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        peer = request.META.get("REMOTE_ADDR", "")
        if peer in settings.TRUSTED_PROXY_IPS:
            try:
                request.client_ip = str(ip_address(request.META["HTTP_X_REAL_IP"]))
            except (KeyError, ValueError):
                return bad_request(request, exception=None)
        else:
            for header in (
                "HTTP_X_FORWARDED_PROTO",
                "HTTP_X_FORWARDED_FOR",
                "HTTP_X_REAL_IP",
                "HTTP_FORWARDED",
            ):
                request.META.pop(header, None)
            request.client_ip = peer
        request.get_host()  # Validate even endpoints which do not render absolute URLs.
        return self.get_response(request)


class ResponseSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Generic complete error pages also cover direct middleware/CSRF/rate-limit
        # responses. Keep status and headers; never wrap JSON, exports or streams.
        if (
            response.status_code >= 400
            and not response.streaming
            and response.get("Content-Type", "").split(";", 1)[0] == "text/html"
        ):
            from config.errors import error_content

            response.content = error_content(response.status_code)
            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))
        response["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "font-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'none'; "
            "object-src 'none'; frame-ancestors 'none'"
        )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["Cache-Control"] = "no-store, private"
        response["Vary"] = "Cookie, HX-Request"
        return response
