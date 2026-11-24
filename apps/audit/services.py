from .models import Event


def record(*, actor, action, obj, previous="", current=""):
    """Explicit fields only: no request bodies, arbitrary metadata or secrets."""
    return Event.objects.create(
        actor=actor if actor and actor.is_authenticated else None,
        action=action,
        object_type=obj._meta.label_lower,
        object_id=str(obj.pk),
        previous_state=previous,
        new_state=current,
    )
