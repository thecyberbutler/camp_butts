# Security architecture

See the threat model and decision register. This implementation is not production-ready.

## Authentication and authorization

Allauth owns username/password authentication, verified email state, recovery, TOTP
and recovery codes. Argon2id uses Django's default 102400 KiB memory, 2 iterations,
8 parallelism; no weaker hash fallback is configured. Passwords accept 15–256
characters, with common-password and user-similarity checks. Axes tracks account
and IP failures independently, with a 15-minute cooloff. Account identifiers are
case-insensitive and database-unique. New accounts are approval-pending campers.

Signup has a uniform completion response and never logs a new user in automatically.
Without SMTP, email recovery and email changes are denied. Email is not implicitly
verified. MFA enrollment requires verified email: an operator can attest independently
verified email ownership using the protected management workflow; approval alone never
verifies an address. Production must document that out-of-band process.

Privileged means staff, superuser, or any account carrying effective permissions.
Every authenticated privileged request requires an enrolled TOTP authenticator and
an MFA record bound to that user by allauth. Enrollment/reauth/logout are narrow
exceptions, not administrative access. Password-only privileged sessions cannot use
the camper endpoints as a bypass. Sensitive staff actions also require a recent
authentication record. No stock Django Admin is mounted.

Owner-filtered queries protect camper reservations and notifications. Service methods
recheck active/approved account state and appropriate permissions inside transactions.
There are no staff overrides of database constraints or policy bypass flags.

## Session and secret protection

Host-only Secure/HttpOnly/Lax cookies; CSRF required; HTTPS retained in development.
Server-side sessions use Django signing plus Fernet encryption, with a separate key,
to protect allauth's temporary enrollment secret while stored in the database.
MFA authenticators and recovery seeds use a distinct Fernet key. Keys are supplied
only as restricted regular files; symlinks, group/world access, missing, short,
low-diversity and recognizable placeholder values are rejected. This cannot prove
randomness; use the generator. The host, runtime memory and operator remain trusted.

Camper session ceilings: 30-minute idle, 12-hour absolute. Privileged: 15-minute idle,
4-hour absolute. Reauthentication window: 5 minutes. Password changes invalidate
Django sessions; security-version and permission stamps revoke sessions on security
changes, approval/privilege changes and MFA changes. Logout destroys the current session.

Never log key material. Framework diagnostics are reduced to category/level/component;
application audit fields are explicitly allowlisted and omit arbitrary bodies/notes.
Proxy/Gunicorn access logs must not record token-bearing paths. Diagnostic detail is
deliberately limited; use synthetic reproduction and audit IDs, never credential dumps.

## Network, database and browser boundaries

Caddy is the only public service. It overwrites scheme/client-IP headers; Django
accepts these only from explicitly configured proxy IPs. PostgreSQL is on a separate
internal network inaccessible to the proxy. Runtime cannot administer schema or roles.
Audit rows allow runtime INSERT/SELECT only. Migrations use separate credentials.

Unified finite daterange occupancy and a PostgreSQL exclusion constraint prevent
reservation/block overlap. Policy and account locks serialize active-count decisions.
Retries are bound to actor and full request payload; notification/audit writes are
transactional. Pending bookings hold inventory until an idempotent expiry command runs.

CSP: no inline/eval scripts; only local scripts/styles; no objects/frames/base URLs;
same-origin forms/connections. `data:` images support allauth's generated TOTP QR.
Templates escape user and administrator text. HTMX evaluation, response scripts and
history cache are disabled. No raw SVG or upload endpoint is exposed.

## Validation and monitoring

Run scripts/security-check.sh plus the PostgreSQL suite. Release also requires image
scans, deployment checks, runtime permission tests, backup restoration, manual access
control/MFA review, accessibility, resource-limit tests and the specification's remaining
acceptance cases. Monitor local audit events, Axes failures, health, disk/memory, scheduled
job exit codes and TLS renewal. Do not send application data to external monitoring.
