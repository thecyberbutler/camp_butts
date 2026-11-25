# Initial threat model

Date: 2026-11-24. Scope: self-hosted multi-campground SaaS, approximately 100 campers
per campground; shared application/database, separate accounts per campground.
This is a design review, not penetration testing or ASVS certification.

## Assets

Password hashes; sessions; TOTP secrets and recovery codes; Django signing and MFA
encryption keys; database and SMTP credentials; invitation secrets; camper contact
data; reservation history and private notes; occupancy integrity; account privileges;
audit history; backups; uploaded media; source, dependencies and deployment images.

## Actors and trust boundaries

Internet visitors and authenticated campers are untrusted. Staff have only assigned
operational permissions; administrators are still untrusted content authors. A stolen
staff session, malicious camper, compromised package, and compromised host are distinct
threats. The host/database administrator remains a trusted root of administration.

1. Browser → Traefik: HTTPS only; bounded requests; no credential-bearing access logs.
2. Traefik → Gunicorn: dedicated private network; proxy overwrites forwarded headers;
   only the proxy may supply trusted client-IP and scheme headers.
3. Django → PostgreSQL: separate internal network; proxy cannot reach DB; SCRAM;
   runtime role cannot change schema, roles or historical audit records.
4. Authentication → application: server-side sessions, account status, mandatory
   privileged MFA, recent authentication, permission and object ownership checks.
5. Runtime → filesystem: non-root, read-only image; narrowly mounted secret files;
   only explicit data/temp paths writable; no Docker socket or host mounts.
6. Operator → migrations/backups: separate credentials and controlled one-shot tools;
   encrypted backups and separately protected recovery keys.
7. Dependency registries → build: trusted upstream sources, locked hashes, audits;
   no source or camper data sent to advisory services.
8. Django → optional approved SMTP: verified TLS; no fallback on delivery failure.

## Threats and controls

| Threat | Required mitigation | Residual risk / verification |
|---|---|---|
| Credential stuffing and enumeration | Argon2id, generic failures, Axes account/IP limits, allauth limits | Distributed abuse and lockout DoS; exercise real login paths |
| Privileged takeover / MFA bypass | Encrypted allauth TOTP, single-use recovery, central gate on every privileged account, no alternate admin login | Host compromise can access keys; exercise every URL |
| IDOR / role escalation | Groups/permissions, server-derived owner, object filtering, no mass assignment | New endpoints need regression tests |
| Stale authorization / session revival | Recheck staff assurance under policy/account locks; bump account security version on activation changes | Raw operator SQL bypasses application serialization; restrict operator access |
| CSRF / XSS / unsafe redirects | Django CSRF and escaping, local assets, strict CSP, safe redirects | Browser/manual review remains required |
| SQL injection / booking races | ORM parameters, unified daterange exclusion, row locks and atomic operations | DB owner can change constraints; DB tests mandatory |
| Inventory hoarding / duplicate submits | Bounded policies, per-account lock, scoped idempotency keys, request limits | Sybil accounts; approval default and operational review |
| Reservation vs maintenance conflict | Both stored in the same constrained occupancy table | Never silently displace a booking |
| Secret disclosure | File injection, generic errors, allowlisted structured audit, no raw request logging | Host admins and memory access remain trusted |
| Malicious uploads / SVG / SSRF | No arbitrary URL fetching; reject raw SVG; controlled map geometry; raster re-encode before any upload feature | Upload feature stays unavailable until validated |
| Database/container compromise | Split roles/networks, no public DB/web ports, non-root/capability drops, encrypted host storage | Full host compromise defeats local isolation |
| Backup theft / stale credentials on restore | Encryption, separate keys, isolated restore drills, session revocation | Operator key loss and historical security state |
| Supply-chain compromise | Poetry hashes, local pinned frontend files, Bandit/pip-audit/Gitleaks/Trivy | Scanners are incomplete; review updates |
| Denial of service | Body/query/pagination limits, proxy timeouts, DB statement timeout, bounded workers | Upstream network exhaustion remains possible |
| Malicious administrator / log tampering | Least privilege, service-only changes, runtime append-only audit | DB/host owners can tamper; protected off-host copies recommended |

## Privacy and retention

Collect only names, email and optional contact phone needed for campground operations.
Never collect payment cards or identity documents. Public map/search expose availability
only. Logs omit bodies, tokens, credentials and private notes. Retention policy and
automated purging must be settled before release; no indefinite collection by default.

## Review triggers

Reassess before enabling uploads, SMTP, administrative routes, public availability,
exports, dependency changes, new networks, backup storage or production deployment.

## Current review findings

The owner-approved Traefik replacement removes the former Caddy dependency paths from
the deployed image. Scans and boundary validation are recorded in implementation progress;
old Caddy findings remain historical evidence. The file provider receives only reviewed
local configuration and exact validated hostnames. No Docker socket/discovery, dashboard,
API or plugins are enabled. Proxy access/debug logging and telemetry remain disabled.

Static serving moves into the existing web boundary with WhiteNoise, restricted to
read-only collected assets; no autorefresh, filesystem finders, uploads or wildcard CORS.
Regression tests exercise traversal, protected headers and requests after startup.
Development CA material stays separate from production ACME state; no private CA key is
stored or mounted. ACME issuance/renewal, certificate expiry monitoring, traffic/load tests,
backup restoration, browser review and SMTP remain open release verification work.

## SaaS threat-model extension

Additional assets: tenant directory/schema bindings, per-campground signing context,
operator provisioning events, activation state and tenant-scoped recovery metadata.
A campground administrator is untrusted with respect to every other campground. Platform
operators and the shared runtime remain separate, broader trust roots.

| Threat | Controls | Residual risk / required evidence |
|---|---|---|
| Changing a URL to impersonate another campground | Resolve active directory entry before auth; schema-local identities/permissions; object checks | URL is public selection, never authorization; cross-tenant HTTP tests |
| Wrong or missing ORM scope; qualified SQL references | Transaction-local search path, no public fallback, FORCE RLS plus restrictive guard | Arbitrary SQL/code execution can change app.tenant; not contained by shared role |
| Identical schema-local IDs confusing authentication | Tenant-bound encrypted sessions and allauth confirmation salts; tenant-bound reset hash input | Shared key compromise affects all tenants; token-collision regressions |
| Process caches or reused connections mixing tenants | Disable content-type instance cache; DB caches per schema; restore context in finally | Review framework upgrades and all future caches/jobs/streams |
| Staff creating tenants or editing platform audit | Directory SELECT only; operator table/sequence inaccessible to app/migrator | Trusted platform/DB administrators can alter directory and audit |
| Cross-tenant backup/restore or stale grants | Explicit UUID/schema backup context; forced RLS; inactive provisioning; grant/activate after migrations | Encrypted multi-tenant restore drill and platform metadata recovery still open |
| One campground exhausting shared resources | Existing proxy/worker/query/lock limits; per-schema booking locks | Aggregate load and fair resource budgets require testing |
| Cross-tenant browser script execution | Strict CSP, escaping, no arbitrary HTML/SVG/scripts, unchanged secure cookies | Paths share origin; host/runtime compromise affects all campgrounds |

Separate runtimes/databases would reduce compromise blast radius; the owner explicitly
selected shared infrastructure. No exemption from existing controls or approval for a
security-reducing workaround is inferred from that selection.
