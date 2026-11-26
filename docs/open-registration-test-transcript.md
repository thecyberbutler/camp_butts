# Open registration and fully enabled test inventory — 2026-11-26

The owner explicitly requested that regular campers need no approval and can register and
reserve immediately. They additionally directed that all campsites on the test instance be
available, with the existing red test banner as the environment notice. SD-031 records the
scope, risks, alternatives, mitigations and rollback. No additional confirmation is required
for these specific instructions. No staff/admin grant is part of this operation.

Use existing registration_mode=open: new local/Google signup creates eligible Camper accounts,
then users sign in normally. Existing duplicate-registration protection, required consent,
verification settings, inactive-account blocks, MFA and rate limits remain. No blanket
approval/reactivation of old accounts or privileged-role changes. Existing reservation
confirmation is already automatic; keep date, capacity, account-limit and concurrency rules.

This exact script refuses production, DEBUG, unexpected baseline policy/inventory or existing
reservations. It locks policy and site rows inside one tenant transaction, opens registration
and booking, enables all 216 sites, audits each change, and verifies expected policy changes.
Site labels retain the map area/identifier but omit inactive-draft descriptions. Test values:
6 guests, RV length 45, 50-amp service, water/sewer and pets allowed. Positions form a distinct
18-column grid. These test values are not verified real-world campsite specifications; the
original reviewed import in source remains unchanged and inactive by default. The test banner
remains; no extra per-site test notice is introduced. No production data is promoted from this
instance, and no production-readiness claim is made. Existing accounts and occupancy remain.

Any exception rolls back policy/site/type/audit writes. For later rollback, an operator may
close booking or return registration to approval through a separately disclosed transaction;
retain accounts, audit and reservations and never remove constraints or silently cancel bookings.
Production onboarding must use authoritative inventory and pass its release gates.

## Exact command, disclosed before connecting

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml exec -T web python -' < /Users/michaelbutler/Repos/camp_butts/.runtime/open-registration-20261126/enable.py
```

Exact stdin script:

```python
"""Owner-authorized test data and open registration; production execution is forbidden."""


def enable():
    from django.conf import settings
    from django.utils import timezone
    from apps.audit.services import record
    from apps.configuration.models import Campground
    from apps.campsites.models import Campsite, CampsiteType
    from apps.reservations.models import Occupancy
    from apps.tenancy.context import lookup, tenant_scope

    if settings.APP_ENVIRONMENT not in {"development", "test"} or settings.DEBUG:
        raise ValueError("Only hardened test/development instances are permitted")
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        policy = Campground.current(lock=True)
        if (
            policy.registration_mode != "approval"
            or policy.booking_enabled
            or policy.approval_required
        ):
            raise ValueError("Unexpected initial policy; review required")
        if not policy.source_import_digest or Occupancy.objects.exists():
            raise ValueError("Expected imported, unused test inventory")
        sites = list(Campsite.objects.select_for_update().order_by("name"))
        if len(sites) != 216 or any(site.active for site in sites):
            raise ValueError("Unexpected inventory baseline")
        kind = CampsiteType.objects.get(name="Unverified map draft")
        if any(
            site.site_type_id != kind.pk or "Inactive draft." not in site.description
            for site in sites
        ):
            raise ValueError("Unexpected site classification or description")
        before = Campground.objects.filter(pk=1).values().get()
        now = timezone.now()
        kind.name = "RV or tent campsite"
        kind.full_clean()
        kind.save(update_fields=["name"])
        record(actor=None, action="operator.test_site_type", obj=kind)
        for index, site in enumerate(sites):
            site.active = True
            # Explicit synthetic test attributes; no claim these describe the real campground.
            site.max_occupancy = 6
            site.max_rv_length = 45
            site.electric_amps = 50
            site.water = site.sewer = site.pets_allowed = True
            site.description = site.description.split("Inactive draft.", 1)[0].strip()
            site.map_x = 50 + (index % 18) * 50
            site.map_y = 50 + (index // 18) * 75
            site.display_order = index + 1
            site.updated_at = now
            site.full_clean()
        Campsite.objects.bulk_update(
            sites,
            [
                "active",
                "max_occupancy",
                "max_rv_length",
                "electric_amps",
                "water",
                "sewer",
                "pets_allowed",
                "description",
                "map_x",
                "map_y",
                "display_order",
                "updated_at",
            ],
        )
        for site in sites:
            record(
                actor=None,
                action="operator.test_site_enabled",
                obj=site,
                previous="inactive",
                current="active",
            )
        policy.registration_mode = "open"
        policy.booking_enabled = True
        policy.full_clean()
        policy.save(update_fields=["registration_mode", "booking_enabled"])
        record(
            actor=None,
            action="operator.registration_mode",
            obj=policy,
            previous="approval",
            current="open",
        )
        record(
            actor=None,
            action="operator.test_booking",
            obj=policy,
            previous="closed",
            current="open",
        )
        expected = {**before, "registration_mode": "open", "booking_enabled": True}
        if Campground.objects.filter(pk=1).values().get() != expected:
            raise ValueError("Unexpected policy change")
        if Campsite.objects.filter(active=True).count() != 216 or Occupancy.objects.exists():
            raise ValueError("Inventory verification failed")
    print(
        "Open registration and booking enabled; all 216 campsites active with test attributes. Existing accounts and reservation constraints unchanged."
    )


if __name__ == "__main__":
    try:
        import django

        django.setup()
        enable()
    except Exception:
        raise SystemExit(
            "Test configuration failed; transaction rolled back and sensitive diagnostics withheld."
        ) from None
```

Status: prepared; execution results follow.

## Public verification commands

```sh
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python .runtime/open-registration-20261126/check_public.py
```

Additional exact public probe:

```python
"""Check public booking entry and red environment banner without printing page content."""
try:
    import requests
    with requests.Session() as browser:
        browser.trust_env = False
        with browser.get(
            'https://camp-butts-test.thecyberbutler.io/c/georgia-mountain-fairgrounds/',
            verify='/etc/ssl/cert.pem', allow_redirects=False, timeout=(5, 15), stream=True,
        ) as response:
            data = bytearray()
            for chunk in response.iter_content(8192):
                data.extend(chunk)
                if len(data) > 65536:
                    raise ValueError('Unexpected page size')
            assert response.status_code == 200
            assert data.count(b'THIS IS A TEST INSTANCE') == 1
            assert b'Explore campsites' in data
            assert b'Online reservations are not open.' not in data
    print('Booking entry is visible, closure notice is absent, and the test banner remains.')
except Exception:
    raise SystemExit('Public booking check failed; sensitive diagnostics withheld.') from None
```

## Execution and validation result

Completed successfully on 2026-11-26. The transaction reported open registration/booking and
all 216 sites active; existing accounts and reservation constraints were unchanged. No role
promotion, image deployment, schema change or secret rotation occurred. Full PostgreSQL suite:
273 passed, 92.74% coverage. Three synthetic operation tests passed, including production refusal
and rollback on audit failure. Ruff/format, Bandit and source/configuration/dependency/secret
gates passed before execution. Public HTTPS/security checks passed after execution; booking
entry is present, the closure notice absent, and the red test banner retained. Actual human
signup/Google consent/new reservation acceptance remains an owner test, not an automated claim.

The previously disclosed rollback guidance preserves accounts/occupancy/audit. Historical
closed-inventory deployment scripts and probes no longer describe the authorized live state.
