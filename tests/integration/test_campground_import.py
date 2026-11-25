import copy
import json
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import Client

from apps.audit.models import Event
from apps.campsites.models import Campsite
from apps.configuration.importing import import_profile, validate_profile
from apps.configuration.models import Campground
from apps.reservations.models import Occupancy
from apps.reservations.services import BookingError, available, book
from apps.tenancy.context import current_tenant

pytestmark = pytest.mark.django_db
SOURCE = Path(__file__).resolve().parents[2] / "data/campgrounds/georgia-mountain-fairgrounds.json"


@pytest.fixture
def profile():
    value = json.loads(SOURCE.read_text())
    tenant = current_tenant()
    value.update(slug=tenant.slug, name=tenant.name)
    value["configuration"]["name"] = tenant.name
    with connection.cursor() as cursor:
        cursor.execute("UPDATE public.campground_tenants SET active=false WHERE id=%s", [tenant.id])
    return value


def test_import_is_atomic_inactive_and_idempotent(profile):
    assert import_profile(profile)
    policy = Campground.current()
    assert policy.min_nights == 2
    assert not policy.booking_enabled
    assert policy.registration_mode == "approval"
    assert not policy.public_availability
    assert Campsite.objects.count() == len(profile["draft_sites"]) == 216
    assert not Campsite.objects.filter(active=True).exists()
    assert Event.objects.filter(action="campground.profile_imported").count() == 1
    Campsite.objects.filter(name="Area II B1").update(description="Reviewed by operator")
    assert not import_profile(profile)
    assert Campsite.objects.get(name="Area II B1").description == "Reviewed by operator"
    assert Event.objects.filter(action="campground.profile_imported").count() == 1


def test_import_rejects_wrong_tenant_and_overwrites(profile, site):
    with pytest.raises(ValidationError):
        import_profile(profile)
    assert Campsite.objects.count() == 1
    assert not Campground.current().source_import_digest
    profile["slug"] = "another-campground"
    with pytest.raises(ValidationError):
        import_profile(profile)


def test_import_rolls_back_all_changes_on_audit_failure(profile, monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("Synthetic audit failure")

    monkeypatch.setattr("apps.configuration.importing.record", fail)
    with pytest.raises(RuntimeError):
        import_profile(profile)
    assert not Campsite.objects.exists()
    assert not Campground.current().source_import_digest
    assert Campground.current().booking_enabled


@pytest.mark.parametrize(
    "unsafe",
    ["javascript:alert(1)", "http://example.test/", "https://name:placeholder@example.test/"],
)
def test_import_rejects_unsafe_links(profile, unsafe):
    profile["configuration"]["map_url"] = unsafe
    with pytest.raises(ValidationError):
        import_profile(profile)
    assert not Campsite.objects.exists()


def test_import_cannot_enable_security_or_booking_options(profile):
    for key, value in (
        ("registration_mode", "open"),
        ("booking_enabled", True),
        ("public_availability", True),
    ):
        altered = copy.deepcopy(profile)
        altered["configuration"][key] = value
        with pytest.raises(ValidationError):
            validate_profile(altered)
    profile["draft_sites"][0]["active"] = True
    with pytest.raises(ValidationError):
        validate_profile(profile)


def test_import_requires_inactive_tenant(profile):
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE public.campground_tenants SET active=true WHERE id=%s", [current_tenant().id]
        )
    with pytest.raises(ValidationError):
        import_profile(profile)


def test_booking_switch_cannot_be_bypassed_by_active_site(policy, camper, site, dates):
    import uuid

    policy.booking_enabled = False
    policy.save()
    with pytest.raises(BookingError):
        book(
            actor=camper,
            campsite_id=site.pk,
            start=dates[0],
            end=dates[1],
            submission_key=uuid.uuid4(),
        )
    assert not Occupancy.objects.exists()
    assert not available(start=dates[0], end=dates[1]).exists()


def test_published_profile_is_escaped_and_does_not_open_inventory(profile):
    profile["configuration"]["welcome"] = '<script>alert("untrusted")</script>'
    import_profile(profile)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE public.campground_tenants SET active=true WHERE id=%s", [current_tenant().id]
        )
    page = Client().get("/c/default/", secure=True)
    assert page.status_code == 200
    assert b"&lt;script&gt;" in page.content
    assert b"<script>alert" not in page.content
    assert b"Online reservations are not open" in page.content
    assert b"$1,000" in page.content and b"$975" in page.content
    assert b"Stays of 2" not in page.content
    assert (
        Client().get("/c/default/campsites/", secure=True).context["page_obj"].paginator.count == 0
    )


def test_import_command_accepts_reviewed_file_and_is_repeatable(profile, tmp_path):
    from io import StringIO

    from django.core.management import call_command

    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile))
    output = StringIO()
    call_command("import_campground", "--file", str(path), stdout=output)
    call_command("import_campground", "--file", str(path), stdout=output)
    assert Campsite.objects.count() == 216
    assert "existing data preserved" in output.getvalue()


@pytest.mark.parametrize("kind", ["invalid", "duplicate", "oversized", "symlink"])
def test_import_command_rejects_unsafe_files_without_echoing_input(profile, tmp_path, kind):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    marker = "untrusted-input-must-not-be-echoed"
    path = tmp_path / "profile.json"
    path.write_text(marker)
    if kind == "duplicate":
        path.write_text('{"name": "' + marker + '", "name": "duplicate"}')
    elif kind == "oversized":
        path.write_text(marker * 10000)
    elif kind == "symlink":
        target = tmp_path / "link.json"
        target.symlink_to(path)
        path = target
    with pytest.raises(CommandError) as error:
        call_command("import_campground", "--file", str(path))
    assert marker not in str(error.value)
    assert not Campsite.objects.exists()


def test_import_test_identity_is_not_allowed_under_production_settings(profile, settings):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    settings.SETTINGS_MODULE = "config.settings.production"
    with pytest.raises(CommandError, match="protected migration identity"):
        call_command("import_campground", "--file", str(SOURCE))
    assert not Campsite.objects.exists()
