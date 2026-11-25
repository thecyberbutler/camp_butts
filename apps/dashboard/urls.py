from django.urls import path

from . import views

urlpatterns = [
    path("campers/", views.camper_accounts, name="camper_accounts"),
    path("campers/<uuid:user_id>/state/", views.account_state, name="account_state"),
    path(
        "site-types/new/", views.classification_create, {"category": "type"}, name="site_type_new"
    ),
    path(
        "amenities/new/", views.classification_create, {"category": "amenity"}, name="amenity_new"
    ),
    path("audit/", views.audit_log, name="audit_log"),
    path("", views.index, name="operations"),
    path("reservations/<uuid:reservation_id>/status/", views.change_status, name="change_status"),
    path("maintenance/", views.maintenance, name="maintenance"),
    path("accounts/", views.accounts, name="account_approvals"),
    path("accounts/<uuid:user_id>/approve/", views.approve, name="approve_account"),
    path("campsites/new/", views.campsite_edit, name="campsite_new"),
    path("campsites/<uuid:site_id>/", views.campsite_edit, name="campsite_edit"),
    path("configuration/", views.configuration, name="configuration"),
    path("calendar/", views.calendar, name="calendar"),
    path("export/", views.export, name="export"),
]
