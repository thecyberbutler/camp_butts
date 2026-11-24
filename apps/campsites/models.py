import uuid

from django.core.validators import MaxValueValidator
from django.db import models


class CampsiteType(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name


class Campsite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, unique=True)
    description = models.TextField(max_length=3000, blank=True)
    site_type = models.ForeignKey(CampsiteType, on_delete=models.PROTECT)
    amenities = models.ManyToManyField(Amenity, blank=True)
    active = models.BooleanField(default=True)
    max_occupancy = models.PositiveSmallIntegerField(default=6)
    max_rv_length = models.PositiveSmallIntegerField(default=0)
    pull_through = models.BooleanField(default=False)
    electric_amps = models.PositiveSmallIntegerField(default=0)
    water = models.BooleanField(default=False)
    sewer = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    pets_allowed = models.BooleanField(default=False)
    accessibility = models.CharField(max_length=500, blank=True)
    map_x = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(1000)])
    map_y = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(1000)])
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_occupancy__gte=1, max_occupancy__lte=100),
                name="campsite_capacity_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(map_x__lte=1000, map_y__lte=1000), name="map_coordinates_valid"
            ),
        ]

    def __str__(self):
        return self.name
