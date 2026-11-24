from django.urls import path

from . import views

urlpatterns = [
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
