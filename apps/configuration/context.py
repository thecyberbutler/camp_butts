from django.conf import settings

from .models import Campground


def campground(request):
    return {
        "campground": Campground.current(),
        "google_login_enabled": request.tenant.slug in settings.GOOGLE_OAUTH_APPS,
    }
