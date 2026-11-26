# Architecture

Django 5.2 LTS / Python 3.13 modular monolith. Apps: accounts, configuration,
campsites, reservations, notifications, audit and tenancy. Server-rendered templates with
locally vendored Bootstrap 5, HTMX (evaluation and response scripts disabled) and
small external JavaScript. The self-hosted SaaS product uses no external managed SaaS,
frontend service or public API.

One occupancy row represents either a reservation or a maintenance block. Its bounded,
nonempty PostgreSQL daterange is canonical; active rows have a GiST exclusion on
(campsite, overlapping range). No second independent source of occupancy truth.
Services own policies, authorization, transitions, locks and audit. Views bind forms
and call services; admin must never edit occupancy directly.

Lock order: configuration → acting/subject accounts in stable primary-key order →
campsite → occupancy. A conservative configuration lock initially serializes policy
mutations and bookings, acceptable at this scale; measure before optimizing. Mutations
and in-app notifications commit atomically. External delivery, when implemented, must
use a durable outbox after commit, never send inside the booking transaction.

Runtime and migration database identities are separate. Provision btree_gist using a
controlled administrator; normal runtime cannot migrate. TLS-only Traefik is the sole
public container. Traefik and PostgreSQL share no network. Host storage encryption and
backup recovery keys are operator responsibilities, not claims made by Docker secrets.

The owner approved replacing Caddy with Traefik on 2026-11-24. Traefik uses only its
file provider: no Docker socket/provider, dashboard, API, plugin, telemetry or new service.
WhiteNoise serves the collected read-only static directory inside the existing Django
container after proxy, HTTPS and response-security middleware. Runtime media/source
finders, autorefresh and wildcard static CORS are disabled. Application caching and
security headers remain unchanged.

Traefik obtains public certificates through ACME TLS-ALPN-01 and stores its account and
private keys in a dedicated 0700 volume/0600 file. Local development uses a short-lived
localhost certificate signed by a separately generated development CA; only the leaf
private key is mounted, and the CA private key is never retained. No TLS bypass is used.

## Campground isolation

The owner selected shared app/database infrastructure and separate accounts per campground.
The existing stack is retained; [the architecture review](saas-architecture.md) compares
schema isolation with a shared-row rewrite and separate deployments. Each schema contains
all domain/authentication/cache/audit tables and their unchanged integrity constraints.
The singleton configuration/policy lock is now per schema, so unrelated campgrounds do
not contend on that lock. Tenant UUID/schema bindings are operator-owned directory records.

The URL is resolved before sessions/authentication. A request transaction sets both
search_path and app.tenant locally; new schemas never fall back to public tables. Forced
row security checks the tenant UUID even for fully qualified queries. No-context production
connections resolve only pg_catalog. Runtime cannot edit the directory or operator events,
change schema, bypass RLS, or mutate audit history. Migrations/jobs explicitly enter a tenant
scope; migration and runtime identities remain separate. Database-backed streaming responses
and asynchronous jobs must establish their own explicit scope before any future introduction.

Disable Django's content-type cache because its database-alias key does not distinguish
schemas. Authentication caches are stored inside each tenant schema. Keep signing/encryption
keys in protected files, bind encrypted sessions and email/reset tokens to the tenant, and
retain __Host cookies. Same-origin URL paths are not independent browser security origins;
CSP/escaping remain mandatory and arbitrary tenant scripts are not supported.

## Public campground profiles and initial import

The mandatory stack remains suitable; no replacement or service split is needed. A bounded
operator-only JSON import populates public contact/rate/rules fields and inactive campsite
drafts inside the selected schema. It never fetches source URLs. A content digest supports
non-destructive retries; atomic audit failure rolls back the entire import.
`booking_enabled` is enforced in reservation policy validation and availability. The
Georgia Mountain Fairgrounds import closes it independently of tenant-directory activation.
See `georgia-mountain-fairgrounds.md`; development-only mutation tooling is separate from
runtime images and documented in `mutation-testing.md`.

## Image distribution

The three existing containers can be built for Linux AMD64/ARM64 and distributed through
owner-approved public Docker Hub repositories. `compose.registry.yaml` replaces only local
build/image selection, preserving the existing deployment boundaries and one-shot jobs.
Versioned source snapshots and verified manifest digest locks identify the artifact; no
managed runtime service or automatic updater is introduced. See `container-publishing.md`.

Deployment identification is independent of runtime security. `APP_ENVIRONMENT` controls
only a shared HTML banner; the public AWS development instance uses production settings and
Gunicorn. Common document/error layouts cover the directory and tenant/auth pages without
requiring tenant/database context to render generic failures. See SD-026.

## Optional Google authentication (SD-027)

The monolith and existing authentication stack are retained. `apps/google_auth` integrates
allauth's Google authorization-code flow with PKCE, OIDC nonce/signature checks and tenant-
bound single-use session state. Google is an explicitly approved external identity dependency.
A private non-root Squid forward proxy permits HTTPS CONNECT only to Google's token and
signing-key hosts; it is infrastructure, not a new application microservice. The web remains
on internal networks; only this optional proxy joins its own outbound network. No DB network,
public ports, Docker socket or application secrets are attached to the proxy.

Every tenant receives allauth socialaccount migrations 0001–0006 and forced RLS. Runtime
cannot access SocialApp credential tables or insert/update SocialToken rows. SELECT/DELETE
on SocialToken are necessary for Django's account-unlink cascade; token storage is disabled
and pending signup drops token objects. Protected per-tenant file configuration is the sole
client-credential source. See [Google operations](google-oauth.md) for deployment/recovery.

## Shared interface presentation

The 2026-11-25 design refresh stays in Django templates and the existing local CSS layer.
Native disclosure elements organize account navigation and long reference text without a
new script dependency. System fonts and fixed local vector artwork keep the existing asset
boundary. Shared allauth layouts/buttons inherit normal authentication forms and controls.
No views, models, authorization logic, database/network boundaries or deployment configuration
change. See `interface-design.md` and SD-028.

Email-only identity (owner request, 2026-11-25) removes the custom user's username column;
UUIDs remain immutable, and email uniqueness remains scoped to each tenant schema. Allauth's
supported email-only settings and a custom Django manager provide local authentication.
Migration validation, session retirement and carried-forward lockouts preserve account
security during cutover. See `email-identity.md`; no automatic account merge or cross-tenant
identity is introduced, and old images are not compatible with the migrated schema.
