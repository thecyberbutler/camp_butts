import uuid

from django.conf import settings
from django.db import models


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=40)
    object_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    outcome = models.CharField(max_length=12, default="success")
    previous_state = models.CharField(max_length=24, blank=True)
    new_state = models.CharField(max_length=24, blank=True)

    class Meta:
        default_permissions = ("view",)
        ordering = ["-created_at"]
