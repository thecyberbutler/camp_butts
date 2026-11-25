# Multi-campground SaaS architecture review

Owner decisions, 2026-11-24: provide a SaaS reservation service; share the application and
PostgreSQL database; retain separate accounts per campground. Managed third-party SaaS,
subscription billing and public APIs are not implied by this change.

## Stack assessment

Retain Python 3.13, Django 5.2 LTS, PostgreSQL/Psycopg, allauth, Argon2id, Axes, templates,
local HTMX/Bootstrap, Poetry, Gunicorn, Docker Compose and Traefik. No replacement framework,
frontend rewrite, microservices, Kubernetes, external identity service or new dependency
is required. Capacity per campground is still initially about 100 campers; tenant count
and aggregate throughput require load testing before production commitments.

A shared-row model would require tenant-aware changes throughout account/email uniqueness,
allauth MFA, session tables, Axes, groups, permissions, invitations and every foreign key.
Schema isolation keeps those existing security/integrity relationships intact, including
PostgreSQL occupancy exclusions, while meeting the owner's shared-database choice.
Separate deployments offer a smaller compromise blast radius but were not selected.

## Boundaries

- A small public directory stores only UUID, validated slug, display name, schema binding
  and activation state. Web has SELECT only; provisioning remains a protected operator action.
- Each campground owns one schema containing all account, MFA, role, session, rate-limit,
  policy, campsite, occupancy, notification, audit and migration tables. No shared identities.
- HTTP selects a tenant before authentication. `?campground=slug` at the directory redirects
  to canonical `/c/slug/` routes. Conflicting, duplicate, absent and unknown selectors fail
  closed. A selector never grants authorization and never directly becomes a SQL identifier.
- Request transactions set the search path and tenant UUID with SET LOCAL and restore nested
  contexts. No public-table fallback is included for new schemas. A separate extension schema
  holds btree_gist; runtime cannot create objects there. Existing campground data can be
  explicitly adopted in public without copying or dropping its constraints.
- FORCE ROW LEVEL SECURITY with a restrictive guard on every tenant table checks the current tenant UUID for reads
  and writes, including qualified references to another schema. Runtime remains non-owner,
  non-superuser, NOBYPASSRLS, with no DDL/role permissions; audit remains append-only.
- Django's database-alias-only content-type cache does not distinguish schemas. Disable that
  small cache through its mapping interface and test cross-schema lookup; do not rely on
  clearing a process-global cache during concurrent requests.
- Encrypted sessions additionally bind their payload to the tenant UUID. Existing sessions
  expire on this upgrade. Confirmation/reset tokens also bind tenant UUID; outstanding legacy
  links become invalid. TOTP issuer labels include the campground. Keep existing __Host Secure/HttpOnly/Lax cookies with Path=/;
  never weaken the prefix to implement path cookies. Initially one active campground login
  per browser cookie jar: switching accounts requires signing in to that campground.
- Campground staff cannot edit the tenant directory, create tenants or grant platform access.
  Existing role/MFA/reauthentication rules apply independently within each schema.

## Residual risks and operational requirements

A shared process/database role and host remain shared trust roots. RLS prevents accidental
unscoped/qualified cross-schema access; it cannot contain arbitrary code execution or SQL
injection able to change connection context. Same-origin paths are not browser security
origins; arbitrary tenant HTML/JavaScript/custom scripts remain prohibited. Separate origins
and runtimes would need a new review if untrusted executable customization is introduced.

Migrations, grants, backups/restores, retention and scheduled jobs must target an explicit
campground. Per-schema upgrades and restores increase operational work; no implicit default
campground is allowed for a command. Aggregate resource contention and upstream DoS remain
shared risks. No isolation against a compromised host/database administrator is claimed.

## Implementation and verification

Implemented and validated: tenant resolution/context, schema provisioning and explicit legacy
adoption, tenant-bound sessions/confirmation/recovery tokens, scoped account links, operator
commands, fresh tenant onboarding, forced RLS and restricted runtime permissions. PostgreSQL
suite: 112 tests passed, 92.51% application coverage. A subsequent focused run passed all 19
tenancy tests, including authenticated cross-tenant reservation/notification denial. The suite
covers shared-ID tokens, separate credentials/roles, invitations, rate limits/cache, connection
context, independent inventory and concurrent bookings across schemas.

Actual runtime probes passed in both directions for adopted public and fresh tenant schemas;
operator-event/sequence access, directory mutation, DDL, audit mutation and migration-history
reads are denied. Local trusted HTTPS selection/branding, proxy/CSRF controls, production
Django checks and migration consistency passed. New tenant provisioning was rehearsed with
synthetic data only; no production data was migrated and no public deployment occurred.

No new dependency or domain Django migration is introduced. Provisioning performs directory,
extension-schema and RLS DDL; existing migrations run independently in every campground schema.
Backup code requires explicit tenant context but its encrypted execution/restore remains
unverified. All unmet release gates remain blockers; no security exception is requested or
inferred. See implementation-progress.md for commands and complete remaining work.

References: [PostgreSQL row security](https://www.postgresql.org/docs/17/ddl-rowsecurity.html),
[Django database boundaries](https://docs.djangoproject.com/en/5.2/topics/db/multi-db/),
[host cookie rules](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie),
[allauth configuration](https://docs.allauth.org/en/latest/account/configuration.html),
[Django transaction scopes](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
