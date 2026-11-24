from django.urls import include, path

from apps.accounts import views as accounts
from apps.campsites import views as campsites
from apps.notifications import views as notifications
from apps.reservations import views as reservations

urlpatterns = [
    path("operations/", include("apps.dashboard.urls")),
    path("accounts/signup/", accounts.SignupView.as_view(), name="account_signup"),
    path(
        "accounts/registration-received/",
        accounts.registration_received,
        name="registration_received",
    ),
    path("", campsites.home, name="home"),
    path("accounts/", include("allauth.urls")),
    path("dashboard/", campsites.dashboard, name="dashboard"),
    path("campsites/", campsites.listing, name="campsites"),
    path("map/", campsites.campground_map, name="campground_map"),
    path("campsites/<uuid:site_id>/", campsites.detail, name="campsite_detail"),
    path("campsites/<uuid:site_id>/reserve/", reservations.book, name="book"),
    path("reservations/<uuid:reservation_id>/", reservations.detail, name="reservation_detail"),
    path("reservations/<uuid:reservation_id>/cancel/", reservations.cancel, name="cancel"),
    path("reservations/<uuid:reservation_id>/modify/", reservations.modify, name="modify"),
    path("notifications/", notifications.index, name="notifications"),
    path(
        "notifications/<uuid:notification_id>/read/",
        notifications.mark_read,
        name="notification_read",
    ),
]
# No stock Django Admin: unrestricted model editing would bypass service policies.
# Dedicated granular operational routes are added only with MFA and audit tests.
