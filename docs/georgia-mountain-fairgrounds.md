# Georgia Mountain Fairgrounds onboarding

Reviewed 2026-11-24. Slug: `georgia-mountain-fairgrounds`. The local validation deployment
contains this real campground profile, separate from earlier synthetic tenants. No public
production deployment or campground account/credential was created.

## Sources and conflicting information

The operator-reviewed JSON at `data/campgrounds/georgia-mountain-fairgrounds.json` records
public facts and provenance from the official [overview](https://georgiamountainfairgrounds.com/pageserver/campgrounds),
[map page](https://georgiamountainfairgrounds.com/pageserver/campground-map),
[rates](https://georgiamountainfairgrounds.com/pageserver/campground-rates), and
[rules](https://georgiamountainfairgrounds.com/pageserver/campground-rules).
These are reference descriptions, not verified live inventory or an executable billing policy.
The application never downloads these URLs; links open the official website explicitly.
No original map artwork or source PDF is copied into application assets.

The overview states 207 sites, while its area totals are 93 + 119 = 212. The map is a
2025-named JPEG with an older illustration copyright. Its labels were transcribed manually
and may contain interpretation errors. The owner explicitly authorized **inactive drafts
from the map**, not activation or treating the map as a verified roster.

The import has **216 inactive drafts**: 93 Area I and 123 Area II. This is a transcription
count, not a claim that 216 rentable sites exist:

- Area I: 1–91, 25A and 56A.
- Area II: A1–A45 and A47; B1–B17; C1–C10; odd D1–D19; E1–E7;
  F1–F10; G1–G5; H1–H15, H17, H19 and H21.

Missing labels were not filled in by guessing a numeric sequence. All labels require
operator verification. Draft capacity defaults, hookup flags and map positions are
explicitly **not specifications**. The internal interactive map is empty while booking
is closed; the public profile links to the official illustrated map.

## Published reference rates

USD; daily / weekly / monthly, as displayed on the rate page:

| Category | Daily | Weekly | Monthly |
|---|---:|---:|---:|
| Area I tent | 35 | 225 | 575 |
| Area I lakeside RV | 50 | 300 | 775 |
| Area I inland RV | 45 | 250 | 675 |
| Area II B1, without sewer | 50 | 325 | 775 |
| Area II lakeside RV | 60 | 400 | 1,000 |
| Area II inland RV | 55 | 350 | 875 |

The linked 2026 rules PDF lists **975** for the Area II monthly lakeside rate, conflicting
with **1,000** above. Both values are flagged for office confirmation. No rate is silently
chosen for charging. The existing platform does not implement payment processing.

The profile includes office phone/address, a concise rules summary, two-night minimum,
check-in/check-out reference times, and office booking/cancellation information. Monthly
stays, seasonal opening windows, deposits, refunds and category pricing require further
policy implementation and authoritative confirmation before online reservations open.

## Import and activation boundaries

The import is bounded, offline, strict-schema, atomic and create-only. It requires the
protected migration DB identity, an explicitly selected inactive campground, matching
name/slug and an empty account/site/reservation store. A canonical content digest makes an
identical retry a no-op, preserving later operator edits; changed imports cannot overwrite
a populated campground. An append-only audit event records completion without raw source data.

All imported campsites remain inactive and `booking_enabled` is false. This server-side
switch denies new reservations and modifications even if a site is accidentally activated;
availability returns no inventory. Cancellation of an existing reservation remains possible.
Registration stays approval-based, public availability stays disabled, and all existing
MFA, authorization, RLS, CSRF, TLS, rate limits and session controls remain in force.
Activating the tenant directory entry does **not** activate booking or campsite drafts.
No web control for opening booking is added by this task.

## Repeatable provisioning

Follow `deployment.md` first: protected secrets, explicit hostname, private PostgreSQL,
built images, and an operator-maintenance window. For a **new** campground only:

```sh
docker compose run --rm provision --create-campground georgia-mountain-fairgrounds --name 'Georgia Mountain Fairgrounds'
docker compose run --rm migrate tenant_command --campground georgia-mountain-fairgrounds migrate --noinput
docker compose run --rm migrate tenant_command --campground georgia-mountain-fairgrounds setup_roles
docker compose run --rm migrate tenant_command --campground georgia-mountain-fairgrounds import_campground --file /app/data/campgrounds/georgia-mountain-fairgrounds.json
docker compose run --rm provision --grant-runtime --campground georgia-mountain-fairgrounds --activate
```

Registering an existing slug is deliberately refused. For upgrades, migrate every existing
schema and reapply runtime grants before restarting the web application. Migration
`configuration.0003_campground_address_campground_booking_enabled_and_more` adds profile
fields, import digest and booking switch. Existing campgrounds retain their prior booking
behavior; the new import explicitly closes this campground.

Select via `/?campground=georgia-mountain-fairgrounds`; canonical path is
`/c/georgia-mountain-fairgrounds/`. Use the deployment's verified HTTPS hostname.
The local validation uses the existing `campground-hardened-validation` project and protected
development CA, with proxy ports bound only to 127.0.0.1:18080/18443.

## Before opening online reservations

Obtain an authoritative roster and confirm each label, capacity, hookups, RV limits,
season, map position and rate category. Reconcile the conflicting counts/monthly rate.
Implement and test monthly/seasonal policies, deposits/cancellations and occupancy blocks
as required; do not reinterpret the current generic defaults as the campground's policy.
Review staff onboarding/MFA and all production release gates. Opening online bookings is
separate controlled work after these requirements are met.
