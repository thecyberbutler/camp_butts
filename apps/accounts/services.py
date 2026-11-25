from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.audit.services import record
from apps.configuration.models import Campground

from .models import User
from .security import lock_staff


def has_privileged_assignments(user):
    # Check assignments even for inactive accounts; get_all_permissions() omits
    # permissions for inactive users and is unsuitable for this target-scope check.
    return (
        user.is_staff
        or user.is_superuser
        or user.user_permissions.exists()
        or user.groups.filter(permissions__isnull=False).exists()
    )


def set_camper_active(*, request, user_id, active):
    if type(active) is not bool:
        raise ValueError("Account state must be a boolean")
    with transaction.atomic():
        Campground.current(lock=True)
        # The policy lock serializes this operation with other account management.
        actor = lock_staff(request, "accounts.manage_camper")
        user = User.objects.select_for_update().get(pk=user_id)
        if user.pk == actor.pk or has_privileged_assignments(user):
            raise PermissionDenied("This operation is limited to ordinary camper accounts.")
        if user.is_active != active:
            previous = "active" if user.is_active else "inactive"
            user.is_active = active
            user.security_version += 1
            user.save(update_fields=["is_active", "security_version"])
            record(
                actor=actor,
                action="account.status_changed",
                obj=user,
                previous=previous,
                current="active" if active else "inactive",
            )
        return user
