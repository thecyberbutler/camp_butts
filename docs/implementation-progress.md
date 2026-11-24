# Implementation progress

Updated: 2026-11-24. Status: development; **not approved for production**.

## Repository assessment

Initially contained only AGENTS.md and PROJECT_SPEC.md, both read in full.
No prior application, architecture, tests, security exceptions, or Git metadata.
Python 3.13 and Poetry are installed. Docker was installed but stopped.
No existing secrets were read. No external hosting or source upload is authorized.

## Phased plan and acceptance evidence

| Phase | Deliverable | Required evidence | State |
|---|---|---|---|
| 0 | Threat model, trust boundaries, security decisions | Document review | Initial design recorded |
| 1 | Poetry/Django/PostgreSQL, custom user, secret files, containers | Startup checks, migrations, lint, scans | In progress |
| 2 | Registration modes, invitations, approvals, allauth, MFA, sessions, Axes | Authentication, abuse, concurrency and privilege tests | Planned |
| 3 | Configuration, campsites, amenities, safe photos | Validation and upload tests | Planned |
| 4 | Unified occupancy, policy services, state transitions | Real PostgreSQL constraints and independent-connection race tests | Planned |
| 5 | Camper search, booking, management, responsive templates | End-to-end flows, CSRF, object authorization | Planned |
| 6 | Controlled SVG map and staff occupancy calendar | Privacy, safe rendering, accessibility | Planned |
| 7 | Granular staff operations, management and exports | MFA, recent authentication, auditing, CSV tests | Planned |
| 8 | In-app notifications, optional SMTP, scheduled work, audit | Transaction and privacy tests | Planned |
| 9 | Hardened deployment, encrypted backup/restore, CI | Container scans, restore rehearsal, runtime role checks | Planned |
| 10 | Release review against every acceptance criterion | All release gates, targeted manual review | Blocked until complete |

## Security status

No security exceptions requested or approved. No existing vulnerability remediated yet.
Dependency versions and advisories are being checked before selection. Release is blocked
until authentication, authorization, MFA, production configuration, secret scans,
dependency scans, real PostgreSQL concurrency tests, and deployment validation pass.
Do not interpret an unexecuted check as a pass.

## Next work

Implement a secure vertical slice through registration, approval, search, booking,
cancellation, maintenance conflicts, notifications and audit. Preserve requirements
when tooling is unavailable and explicitly record unverified behavior.
