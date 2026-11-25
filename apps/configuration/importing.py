"""Offline, create-only import of reviewed public campground information."""

import hashlib
import json
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record
from apps.campsites.models import Campsite, CampsiteType
from apps.reservations.models import Occupancy
from apps.tenancy.context import current_tenant, lookup

from .models import Campground
from .validators import public_https_url

CONFIG_FIELDS = {
    "name",
    "welcome",
    "address",
    "contact_phone",
    "website_url",
    "map_url",
    "rate_information",
    "rules",
    "reservation_policy",
    "policy_version",
    "min_nights",
}


def validate_profile(profile):
    if (
        not isinstance(profile, dict)
        or set(profile)
        != {
            "format_version",
            "slug",
            "name",
            "reviewed_on",
            "sources",
            "configuration",
            "draft_sites",
            "notes",
        }
        or type(profile["format_version"]) is not int
        or profile["format_version"] != 1
    ):
        raise ValidationError("Invalid campground import format.")
    config = profile["configuration"]
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValidationError("Import contains unsupported configuration fields.")
    if any(not isinstance(config[key], str) for key in CONFIG_FIELDS - {"min_nights"}):
        raise ValidationError("Import text fields must be strings.")
    if type(config["min_nights"]) is not int:
        raise ValidationError("Minimum nights must be an integer.")
    if config["name"] != profile["name"]:
        raise ValidationError("Campground names do not match.")
    try:
        date.fromisoformat(profile["reviewed_on"])
    except (ValueError, TypeError):
        raise ValidationError("A valid source review date is required.") from None
    if not isinstance(profile["sources"], list) or not 1 <= len(profile["sources"]) <= 10:
        raise ValidationError("Bounded source references are required.")
    for url in profile["sources"]:
        if not isinstance(url, str) or not url or len(url) > 500:
            raise ValidationError("Invalid source link.")
        public_https_url(url)
    if not isinstance(profile["notes"], list) or len(profile["notes"]) > 20:
        raise ValidationError("Invalid source notes.")
    if any(not isinstance(note, str) or len(note) > 1000 for note in profile["notes"]):
        raise ValidationError("Invalid source note.")
    sites = profile["draft_sites"]
    if not isinstance(sites, list) or len(sites) > 500:
        raise ValidationError("At most 500 draft sites can be imported.")
    names = set()
    for site in sites:
        if not isinstance(site, dict) or set(site) != {"name", "area", "map_label"}:
            raise ValidationError("Only draft map identifiers are accepted.")
        if any(
            not isinstance(value, str) or not value.strip() or len(value) > 60
            for value in site.values()
        ):
            raise ValidationError("Invalid draft map identifier.")
        if site["name"] in names:
            raise ValidationError("Duplicate draft campsite name.")
        names.add(site["name"])
    return hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()


@transaction.atomic
def import_profile(profile):
    digest = validate_profile(profile)
    tenant = current_tenant()
    if profile["slug"] != tenant.slug or profile["name"] != tenant.name:
        raise ValidationError("Import must match the explicitly selected campground.")
    policy = Campground.current(lock=True)
    if policy.source_import_digest == digest:
        return False
    registered = lookup(tenant.slug, include_inactive=True)
    if registered is None or registered.active:
        raise ValidationError("Initial import requires an inactive campground.")
    if (
        policy.source_import_digest
        or User.objects.exists()
        or Campsite.objects.exists()
        or Occupancy.objects.exists()
    ):
        raise ValidationError("Initial import cannot overwrite existing campground data.")
    for key, value in profile["configuration"].items():
        setattr(policy, key, value)
    # Import cannot open registration/availability, enable booking, or grant privileges.
    policy.booking_enabled = False
    policy.source_import_digest = digest
    policy.full_clean()
    policy.save()
    kind, _ = CampsiteType.objects.get_or_create(name="Unverified map draft")
    for draft in profile["draft_sites"]:
        site = Campsite(
            name=draft["name"],
            site_type=kind,
            active=False,
            max_occupancy=1,
            description=(
                f"{draft['area']}, published map label {draft['map_label']}. "
                "Inactive draft. Capacity, vehicle limits, hookups, season and map "
                "position are unverified; numeric defaults are not site specifications."
            ),
        )
        site.full_clean()
        site.save()
    record(actor=None, action="campground.profile_imported", obj=policy)
    return True
