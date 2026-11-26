# Implementation progress

Updated: 2026-11-26. Status: development; **not approved for production**.

Latest milestone: scanned email-only/Google-profile prerelease
`0.1.0-alpha.20261125-05df000f8652` published and deployed to the AWS test instance. Final
runtime/public acceptance passed 2026-11-26; human Google consent/profile import is unverified.
See the final milestone below for current evidence, file inventory and remaining gates.
Earlier sections preserve historical state and approvals; they do not override SD-025–030.

## Repository assessment

Initially contained only AGENTS.md and PROJECT_SPEC.md, both read in full.
No prior application, architecture, tests, security exceptions, or Git metadata.
Python 3.13 and Poetry are installed. Docker is now running for isolated validation.
The owner initialized Git; initial implementation is in commit `af3241c`.
No existing secrets were read. No external hosting or source upload is authorized.

## Phased plan and acceptance evidence

| Phase | Deliverable | Required evidence | State |
|---|---|---|---|
| 0 | Threat model, trust boundaries, security decisions | Document review | Initial design recorded |
| 1 | Poetry/Django/PostgreSQL, custom user, secret files, containers | Startup checks, migrations, lint, scans | Implemented; application/database/proxy image gates passed |
| 2 | Registration modes, invitations, approvals, allauth, MFA, sessions, Axes | Authentication, abuse, concurrency and privilege tests | Core implemented and tested; recovery/management work remains |
| 3 | Configuration, campsites, amenities, safe photos | Validation and upload tests | Models/management implemented; uploads unavailable |
| 4 | Unified occupancy, policy services, state transitions | Real PostgreSQL constraints and independent-connection race tests | Core implemented and tested; overrides and remaining policy cases pending |
| 5 | Camper search, booking, management, responsive templates | End-to-end flows, CSRF, object authorization | Implemented/tested core workflow; browser/accessibility review pending |
| 6 | Controlled SVG map and staff occupancy calendar | Privacy, safe rendering, accessibility | Implemented/tested bounded views; richer filtering pending |
| 7 | Granular staff operations, management and exports | MFA, recent authentication, auditing, CSV tests | Partial; approvals, camper activation, classifications, audit viewer, policies, statuses, maintenance and occupancy export implemented |
| 8 | In-app notifications, optional SMTP, scheduled work, audit | Transaction and privacy tests | Transactional in-app notifications/audit and expiry implemented; SMTP delivery validation/reminders pending |
| 9 | Hardened deployment, encrypted backup/restore, CI | Container scans, restore rehearsal, runtime role checks | Isolated HTTPS deployment validated; Traefik deployment validated; backup/CI and other release work remains |
| 10 | Release review against every acceptance criterion | All release gates, targeted manual review | Blocked until complete |

## Security status

No security exceptions requested or approved. The initial 52 web and 145 PostgreSQL
high/critical package/advisory pairs were addressed in replacement images; fresh scans
and runtime validation passed. The owner-approved Traefik replacement removes the former
Caddy component; final proxy/application HIGH/CRITICAL scans passed. See
`security-findings.md` for the full unsuppressed history and residual risk.
Release is blocked
until authentication, authorization, MFA, production configuration, secret scans,
dependency scans, real PostgreSQL concurrency tests, and deployment validation pass.
Do not interpret an unexecuted check as a pass.

## Validation evidence

- 93 tests passed on hardened PostgreSQL 17.12; measured application coverage 92.20% (settings and generated migrations excluded).
- Independent connections cover overlapping bookings, maintenance races, duplicate submissions,
  account limits, competing modifications, direct constraint enforcement, final invitation use,
  and concurrent shared-cache authentication rate limiting.
- Real password/TOTP login and single-use recovery codes tested; no MFA bypass setting used.
- CSRF-protected booking/modification/cancellation workflow, IDOR, XSS, role gates and CSV protection tested.
- Ruff check/format, Bandit and Poetry lock validation passed; Poetry reports metadata deprecations.
- pip-audit found no known vulnerabilities in the installed application/development dependency set.
- Gitleaks passed on both the current Git history and final source review copy (including new files).
- Trivy final source/lock and all three Dockerfiles passed HIGH/CRITICAL gates. Final web and
  hardened database images passed their HIGH/CRITICAL gates. The final Traefik image also passed.
- Separate migration credentials initialized PostgreSQL; runtime grants deny DDL, migration-history reads,
  and audit mutation. Production Django deployment checks passed with zero silenced findings.
- Fresh non-root, all-capabilities-dropped PostgreSQL initialization, separate provisioning, role setup,
  migration consistency and static collection passed. Both the earlier Caddy deployment and replacement Traefik
  deployment served verified HTTPS. Traefik boundary checks passed using the
  real local CA with certificate verification enabled. No public deployment was performed.
- Backup/restore drill, SMTP, host hardening, full browser/accessibility/performance/manual security review
  and the complete specification acceptance matrix remain unverified.

## Next work

1. Validate public ACME issuance/renewal, expiry monitoring and measured proxy/static-serving load.
2. Complete encrypted backup/restore drills, safe key rotation, retention and lost-MFA recovery procedures.
3. Add reviewed local/reproducible CI with image/security gates; hash-lock and scan the builder toolchain.
4. Complete profile, registration/invitation management, staff booking/edit/override workflows,
   safe raster uploads, notifications/reminders and remaining reporting/map features.
5. Validate SMTP with approved egress and verified TLS; complete browser/accessibility/load tests.
6. Review every specification acceptance criterion, host controls and manual security tests before release.

No security-reducing alternative is proposed; no approval is pending. Keep unresolved
gates visible and never infer release approval from test coverage.

## This continuation's changes and security impact

- Added granular ordinary-camper activation/deactivation, classification creation and audited audit viewing.
- Rechecked privileged assurance under locks for administrative mutations and exports; protected inactive
  privileged targets and revoked sessions on both deactivation and reactivation. Role setup shares the policy lock.
- Added regression tests for stale authorization, session revival and concurrent rate limiting.
- Added a repeatable runtime database boundary probe; protected operations must return PostgreSQL 42501.
- Replaced vulnerable application/database image contents, preserved SCRAM and role boundaries,
  removed unused runtime installers/helpers, and required positive non-root image identities.
- Kept original scratch database volumes; fresh-volume validation avoids physical cross-libc migration.
- Added complete locked dependency inventory and retained all original image findings with disposition.
- New migration: `accounts/0002_alter_user_options.py` adds `manage_camper` permission metadata.
  Run `migrate`, then reviewed `setup_roles`; existing account sessions detect permission changes.
- No Python/frontend dependency or lockfile changed in this continuation. Docker bases changed as recorded
  in dependency inventory. No security exception, public deployment, Git commit or push was performed.
- No known security-control regression was accepted. Alpine compatibility is tested for current flows,
  but collation/base-OS migration and untested release criteria remain operational risks.

Validation commands and environment setup are in README.md and docs/deployment.md. Native
scanner orchestration as a whole, CI, backup/restore, SMTP, browser/accessibility/performance
review, host hardening and full release acceptance remain unverified. Individual checks
listed above were actually run; no skipped gate is described as passed.

## Modified and added files in this continuation

- `Dockerfile`
- `Dockerfile.db`
- `Dockerfile.proxy`
- `README.md`
- `apps/accounts/migrations/0002_alter_user_options.py`
- `apps/accounts/models.py`
- `apps/accounts/security.py`
- `apps/accounts/services.py`
- `apps/configuration/management/commands/setup_roles.py`
- `apps/dashboard/forms.py`
- `apps/dashboard/urls.py`
- `apps/dashboard/views.py`
- `compose.yaml`
- `docs/administration.md`
- `docs/dependency-inventory.md`
- `docs/deployment.md`
- `docs/implementation-progress.md`
- `docs/security-decisions.md`
- `docs/security-findings.md`
- `docs/security.md`
- `docs/threat-model.md`
- `scripts/check_database_boundary.py`
- `scripts/provision_test_db.py`
- `scripts/test.sh`
- `templates/dashboard/audit.html`
- `templates/dashboard/campers.html`
- `templates/dashboard/operations.html`
- `tests/concurrency/test_rate_limits.py`
- `tests/security/test_account_management.py`
- `tests/security/test_accounts.py`
- `tests/security/test_mutation_authorization.py`

The owner-created local editor settings directory was left untouched. The isolated HTTPS validation
stack and superseded test database are stopped; their volumes remain intact. The hardened
test database remains available on loopback port 55433 for the documented test commands.

## Owner-requested Traefik replacement — 2026-11-24

Architectural approval: “lets replace Caddy with Traefik”. This approval does not waive
any security requirement. Current phase: deployment hardening, with application feature
and release work still outstanding. No security-reducing exception or pending approval.

Completed:

- Replaced the Caddy image/configuration with digest-pinned Traefik 3.7.20; removed both Caddyfiles.
- Preserved three containers, exact hosts, HTTPS/secure cookies/CSRF/CSP, private networks,
  non-root execution, read-only filesystems, dropped capabilities, request limits and timeouts.
- File-provider routing only; no Docker socket/provider, dashboard/API, plugins or telemetry.
- Added locked WhiteNoise 6.12.0 (MIT; no required transitive dependencies) for collected,
  read-only static assets, retaining response controls and rejecting traversal/autorefresh/CORS.
- Added protected localhost-only certificate generation and deployment-boundary validation.
  Corrected missing certificate key identifiers without weakening TLS verification.
- Production ACME state is isolated in a new protected volume. Old Caddy volumes are preserved.
- Added actual container startup refusal tests and static/TLS security regression tests.
  Tests collect assets into a temporary directory instead of suppressing missing-directory warnings.
- Updated the owner-authorized stack requirements, architecture, threat model, decisions,
  dependency inventory, findings, deployment, backup and incident-response guidance.

Validation: 93 tests passed, 92.20% application coverage, real PostgreSQL concurrency;
Ruff/format/Bandit/Poetry lock validation passed (Poetry metadata deprecation warnings remain).
Full installed pip-audit found no known findings. Final web and Traefik image HIGH/CRITICAL
scans passed. Production Django checks and runtime DB-denial probes passed. The live proxy
check verified certificate trust, HTTP redirect, static files/security headers, forwarding
spoof rejection, unknown hosts/SNI, body limits, CSRF and no exposed dashboard/API.

No database migration is introduced by this proxy task. Public-domain ACME issuance/renewal,
expiry alerts, browser/accessibility/load testing, SMTP, encrypted backup/restore and full
release acceptance remain unverified. The application is not production-ready.

Modified/added by the proxy task: `.dockerignore`, `AGENTS.md`, `PROJECT_SPEC.md`,
`Dockerfile.proxy`, `compose.yaml`, `compose.dev.yaml`, `pyproject.toml`, `poetry.lock`,
`config/settings/base.py`, `infra/traefik/{entrypoint.sh,traefik.yaml,traefik.dev.yaml,dynamic.yaml}`,
`scripts/{generate_dev_tls.py,check_proxy_boundary.py}`, `tests/conftest.py`,
`tests/security/{test_static_and_tls.py,test_proxy_startup.py}`, `README.md`, `SECURITY.md`,
`docs/{architecture,security,threat-model,security-decisions,implementation-progress,deployment,
dependency-inventory,security-findings,backup-and-restore,incident-response}.md`.
Removed: `Caddyfile`, `Caddyfile.dev`. Earlier application changes and owner local editor settings remain intact.

Final proxy-task checks: source/lock/Dockerfile HIGH/CRITICAL scan and Gitleaks source scan
passed; production and development Compose configurations and migration consistency
passed. Unknown SNI was verified to trigger a server-side TLS rejection, not merely a
client hostname mismatch. The scratch validation stack is stopped with volumes intact.
No public ACME request, public deployment, Git commit or push was performed.

Repeatable checks after the documented build/setup:

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --cov --cov-fail-under=85
.venv/bin/python scripts/check_proxy_boundary.py --ca-file .secrets/dev-tls/ca.crt \
  --https-port 18443 --http-port 18080 --campground pine-grove
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/pip-audit --progress-spinner off
```

The live boundary check requires starting the isolated stack first. Public ACME issuance
and renewal, load testing and the broader release gates listed above remain unexecuted;
there is no claim that those gates passed.

## SaaS implementation — 2026-11-24

Owner choices: shared application/PostgreSQL database, separate accounts per campground.
Architecture review is in saas-architecture.md. The mandatory stack remains suitable;
no replacement technology or new dependency is required. No security exception or
pending security approval exists. Current phase: multi-campground isolation implemented;
recovery/operational release validation remains open. This is not production-ready.

### Phased SaaS plan and outcome

| Phase | Work | Outcome |
|---|---|---|
| S1 | Review stack, account model, assets, trust boundaries and threat model | Completed; schema-per-campground selected within shared infrastructure |
| S2 | Protected tenant directory, explicit URL resolution, transaction-local context and database isolation | Implemented; FORCE RLS plus restrictive guard; legacy public-schema adoption and fresh provisioning validated with synthetic data |
| S3 | Isolate identity/MFA/cache, bind sessions and tokens, preserve routes and authorization | Implemented/tested; duplicate identifiers remain independent; allauth token collision and content-type cache hazards corrected |
| S4 | Scope booking, staff, notification, invitation and job workflows; test concurrent tenants | Implemented via schema boundaries and explicit command wrapper; existing workflow/concurrency suite retained |
| S5 | Deployment, scanning, backup/restore, resource isolation and release acceptance | Provisioning/runtime/HTTPS/scanner checks pass as recorded below; encrypted recovery, load and broader release gates remain unverified |

### Completed functionality and architectural/security decisions

- Public active-campground directory and `?campground=slug` selection redirect to `/c/slug/`.
  Missing/unknown/disabled/duplicate/conflicting contexts fail closed. Selection never grants access.
- Separate schema-local accounts, email/username uniqueness, groups, MFA/recovery, caches,
  sessions, policies, campsites, reservations, notifications and append-only audit history.
- Transaction-local schema/UUID scope includes authentication, rendering and session writes.
  New tenant schemas have no public fallback; unscoped production connections use pg_catalog.
- FORCE RLS plus a restrictive tenant guard denies incorrect or absent context, including
  qualified references. Runtime remains non-owner/NOBYPASSRLS with no DDL or directory writes.
  Operator events and sequence are inaccessible to runtime/migrator identities.
- Sessions, email confirmations and reset tokens bind the tenant UUID using existing signing/
  encryption primitives; no legacy acceptance fallback. TOTP issuer labels identify the campground.
  Existing secure __Host cookie flags/paths, session ceilings, MFA, CSRF, CSP and rate limits remain.
- Django's content-type cache is disabled to prevent cross-schema instance reuse. Security caches
  and failed-login counters remain independent. Staff privileges do not become platform privileges.
- Operator register/adopt → migrate → roles → protect/grant → activate lifecycle. Activation
  requires required tables; existing misprivileged DB roles and incompatible CLI options fail closed.
  New tenant branding is initialized once; existing branding/data/constraints are preserved.
- Explicit campground wrapper for migrations, role/account/invitation operations, session cleanup
  and reservation expiry. Per-campground policy locks allow independent concurrent bookings.
- Backup workflow selects a registered UUID/schema with RLS enabled and encrypts metadata;
  shell syntax validated only. Full encrypted execution and restoration are not claimed.

Migration impact: no new domain Django migration. Operator provisioning creates the directory/
event/extension schemas and row-security policies; all existing Django migrations run in each
new schema. Existing public data can be explicitly adopted without dropping constraints or
copying it. Sessions and pending verification/reset links are invalidated by this upgrade.
No Python/frontend dependency or lockfile change belongs to this SaaS task.

### Validation evidence

- Full PostgreSQL 17.12 suite: **112 passed**, **92.51%** application coverage (settings and
  generated migrations excluded). Existing independent-connection booking/maintenance,
  idempotency, policy, invitation and rate-limit race tests remain enabled.
- All **19 tenancy tests** passed again after adding authenticated cross-tenant reservation,
  notification and staff-access assertions. Includes separate accounts; HTTP selectors; signed
  confirmation/reset collisions; copied session payloads; invitation rejection; cache/rate limits;
  content types; disabled tenants; qualified SQL read/write denial; missing context; restrictive
  policy composition; nested context cleanup; independent and concurrent inventory.
- Actual web database role probes passed in both directions between adopted public and fresh
  schemas; fresh third-tenant probes also passed. Directory writes, platform operator table and
  sequence access, DDL, audit updates/deletes and migration-history reads are denied.
- Synthetic fresh onboarding completed through migrations, roles, grants and activation.
  Verified HTTPS directory selection, initial branding and campground-specific account links.
- Live local-CA HTTPS proxy checks passed: trust/hostname, SNI/host denial, headers, static
  boundaries, forwarding spoof protection, request sizes and CSRF. No TLS bypass was used.
- Production Django checks: zero issues, zero silenced findings. Tenant-scoped migration
  consistency: no changes. Production/development Compose syntax and Git whitespace checks passed.
- Ruff check/format, Bandit, Poetry lock checks passed; Poetry metadata deprecation warnings remain.
  Bandit's import-path false positive is narrowly annotated and reviewed in security-findings.md.
- Refreshed pip-audit: no known vulnerabilities. Source-only Gitleaks and web image HIGH/CRITICAL
  scan passed; final source/lock/Dockerfile HIGH/CRITICAL scan also passed. Database/proxy
  base images and dependencies are unchanged from their previously recorded passing scans.
- Backup shell syntax passed. Encrypted backup/restore, platform metadata recovery and recovery
  time objectives were **not** validated; neither are SMTP, public ACME renewal, aggregate load,
  browser/accessibility review, complete CI/toolchain gates or all specification acceptance cases.

### Security findings, impacts and remaining work

Resolved integration hazards: cross-tenant allauth confirmation signature reuse, shared
content-type cache entries, draft operator-audit grants and permissive-policy composition.
See security-findings.md for evidence and the reviewed Bandit false positive. No known
security-control regression was accepted; no security approval is pending.

Shared runtime/database credentials/encryption keys/host remain common trust roots: arbitrary
SQL or process compromise can affect all tenants. RLS is defense against missing/wrong query
context, not a boundary against code execution that changes context. Paths share a browser
origin; untrusted executable customization remains prohibited. One campground login per
browser cookie jar is supported initially. Tenant count/aggregate capacity is unmeasured.

Next steps:

1. Rehearse encrypted per-tenant and platform metadata backups/restores; compare row counts,
   verify occupancy/authentication state and revoke stale sessions/tokens before activation.
2. Validate aggregate load/resource fairness, host controls, monitoring, ACME renewal and SMTP.
3. Complete remaining existing feature/release work: lost-MFA recovery, retention, safe uploads,
   profiles/invitation management, audited staff edits/overrides, reminders, richer reports/maps,
   CI/toolchain scanning, browser/accessibility and complete manual security acceptance.
4. Review operator lifecycle and recovery before production rollout; no billing, public API,
   automatic campground self-onboarding or external managed service was introduced.

### Files changed by the SaaS task

- `AGENTS.md`, `PROJECT_SPEC.md`, `README.md`, `SECURITY.md`, `.dockerignore`, `Dockerfile`, `compose.yaml`.
- `apps/tenancy/__init__.py`, `apps/tenancy/apps.py`, `apps/tenancy/allauth.py`,
  `apps/tenancy/context.py`, `apps/tenancy/middleware.py`, `apps/tenancy/management/__init__.py`,
  `apps/tenancy/management/commands/__init__.py`, `apps/tenancy/management/commands/tenant_command.py`.
- `apps/accounts/adapters.py`, `apps/accounts/tokens.py`, `apps/configuration/models.py`.
- `config/sessions.py`, `config/settings/base.py`, `config/settings/testing.py`.
- `scripts/tenant_database.py`, `scripts/provision_database.py`, `scripts/provision_test_db.py`,
  `scripts/runtime_grants.sql`, `scripts/check_database_boundary.py`, `scripts/check_proxy_boundary.py`,
  `scripts/backup.sh`.
- `templates/base.html`, `templates/tenancy/directory.html`.
- `tests/conftest.py`, `tests/security/test_tenancy.py`, `tests/security/test_accounts.py`,
  `tests/security/test_account_management.py`, `tests/security/test_http.py`,
  `tests/security/test_mutation_authorization.py`, `tests/security/test_staff.py`,
  `tests/integration/test_workflows.py`, `tests/concurrency/test_invitations.py`,
  `tests/concurrency/test_races.py`, `tests/concurrency/test_rate_limits.py`. Existing
  tests now use explicit `/c/default/` URLs or explicitly scoped independent connections.
- `docs/saas-architecture.md`, `docs/architecture.md`, `docs/security.md`, `docs/threat-model.md`,
  `docs/security-decisions.md`, `docs/security-findings.md`, `docs/deployment.md`,
  `docs/administration.md`, `docs/backup-and-restore.md`, `docs/incident-response.md`,
  `docs/dependency-inventory.md`, `docs/implementation-progress.md`.

Earlier application and Traefik changes remain intact. Owner local editor settings were not edited.
No public deployment, production-data migration, Git commit or push was performed.

### Repeatable validation and unexecuted release checks

After the protected setup in README/deployment, from the repository root:

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --cov --cov-fail-under=85
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/pip-audit --progress-spinner off
poetry check --lock
bash -n scripts/backup.sh
docker compose exec web python manage.py check --deploy --fail-level WARNING
docker compose run --rm migrate tenant_command --campground pine-grove makemigrations --check --dry-run
docker compose exec -T web python - --campground pine-grove --other-campground lake-view < scripts/check_database_boundary.py
.venv/bin/python scripts/check_proxy_boundary.py --ca-file .secrets/dev-tls/ca.crt \
  --campground pine-grove --https-port 18443 --http-port 18080
```

Use the matching Compose project/overlay and actual registered slugs for live checks;
the documented scratch stack binds only loopback. Scanner orchestration also requires
reviewed Gitleaks/Trivy binaries or the digest-pinned restricted containers used in validation.

Still unexecuted: `bash scripts/backup.sh` with the protected tenant backup configuration;
`CONFIRM_ISOLATED_RESTORE=YES bash scripts/restore.sh SNAPSHOT /new/protected/staging`,
followed by the isolated tenant/platform DB restoration procedure. Do not run those against
production until reviewed. Public ACME renewal, SMTP, load, manual browser/accessibility
and release security acceptance need their environment-specific rehearsals; no fabricated
one-command verification is provided for them.


Final SaaS scan results: source/lock/Dockerfile HIGH/CRITICAL checks and final application
image HIGH/CRITICAL checks passed with zero findings at those severities; final source-only
Gitleaks passed. All planned automated checks above completed. The isolated HTTPS validation
stack is stopped with volumes retained; the hardened PostgreSQL test service remains available
on loopback port 55433. No production readiness or release approval is implied.

## Georgia Mountain Fairgrounds onboarding and mutation testing — 2026-11-24

Current phase: real campground reference/profile onboarding and test adequacy hardening.
The existing required stack remains appropriate; no runtime technology replacement is needed.
Earlier SaaS/Traefik work and owner editor files were preserved. No public deployment,
production-data migration, commit or push was performed.

### Completed functionality and architecture

- Provisioned `georgia-mountain-fairgrounds` in the local `campground-hardened-validation`
  PostgreSQL deployment, with independent schema/account namespace, forced RLS and existing
  least-privileged runtime grants. Prior synthetic tenants/data are retained.
- Imported official public contact/address, overview, rules, policy and reference rates;
  safe HTTPS links point to the official overview/map. No source PDF/map artwork or credential
  is copied to application assets. All displayed text is escaped.
- Created **216 inactive map drafts**, explicitly authorized by the owner: 93 Area I and
  123 Area II. They are unverified identifiers, not a verified count of available campsites.
  Published 207 vs 212 totals and $1,000 vs $975 monthly lakeside rates remain unresolved.
- Added bounded, strict-schema, offline migration-identity import with duplicate-key/file
  validation, tenant/name matching, inactive/empty tenant checks, atomic audit and no-op
  digest retries. Existing data and later edits cannot be overwritten by another import.
- Added server-side booking closure and availability closure; imported drafts stay inactive.
  Tenant directory activation publishes the profile but does not open booking. No users,
  default credentials, privilege grants or security setting changes are imported.
- Added exact **mutmut 3.8.1** development dependency and eight reviewed transitive packages.
  Runtime dependencies/images contain no mutmut. The wrapper uses private source copies,
  disposable synthetic PostgreSQL databases, forkserver, one worker, bounded execution,
  discarded raw output and sanitized status-only reports. No application mutant was applied.
- Added import security/atomicity/idempotence/booking tests and reservation date-boundary,
  invalid-type and inclusive-arrival/exclusive-departure tests.

### Security decisions, findings and approvals

SD-023 and SD-024 document import and mutation boundaries. Existing TLS, MFA, authorization,
CSRF, CSP, session lifetimes, password hashing, rate limits, tenant RLS, occupancy constraints
and container isolation remain. No new runtime permissions or publicly exposed service.
No pending security approval and no security exception requested/granted/inferred.
Development tooling adds dependency surface; pins, audits, runtime exclusion and isolated
synthetic-data execution mitigate it. This wrapper is not an OS sandbox for hostile code.

A Wi-Fi credential in the official linked PDF was excluded from imports and all repository
artifacts; only type/location is recorded in `security-findings.md`. Upstream publication
remains unresolved externally. Mutation findings were **testing gaps**, not observed defects
in the existing date validator; six additional mutants are now rejected by meaningful tests.
No new application vulnerability is known, and no exhaustive security claim is made.

### Validation actually executed

- Full PostgreSQL suite: **144 passed**, **92.35%** coverage; includes existing security,
  tenancy and independent-connection concurrency tests. Final run had no warnings.
- First date-range mutation campaign: **23 executed, 13 killed, 10 survived**.
  After boundary/type tests: **23 executed, 19 killed, 4 survived**, no runner errors or
  timeouts. Three survivors alter message presentation; one removes the explicit `[)`
  argument whose Psycopg default is identical. All remain visible; wrapper correctly exits
  nonzero requiring review. Neither 100% mutation success nor whole-application coverage
  is claimed. Reports are ignored/private `.runtime/mutation/run-*/summary.json`.
- Configuration migration 0003 applied to all three preexisting local tenants and the new
  campground. Runtime grants reapplied; initial import/activation and identical retry passed.
- Live restricted runtime checks: 216 inactive sites, booking closed, approval registration,
  private availability, zero accounts, exactly one import audit; runtime import denied;
  mutmut absent. Cross-schema reads/writes and protected DB operations denied.
- Verified-CA HTTPS proxy check passed for the new tenant: assets, security headers,
  host/SNI rejection, body-size limits and CSRF enforcement.
- Ruff checks/format, Bandit and Poetry lock consistency passed. Poetry reports existing
  legacy metadata deprecation notices; no lock inconsistency. Two narrow reviewed subprocess
  Bandit annotations are explained in SD-024, with no broad rule suppression.
- Candidate and final installed dependency pip-audit: no known vulnerabilities.
- Final rebuilt image/source scans and final deployment/migration checks are recorded below
  after completion; earlier scan results are not substituted for current evidence.

### Migration, dependencies and files changed in this task

Migration: `apps/configuration/migrations/0003_campground_address_campground_booking_enabled_and_more.py`.
Adds seven profile/booking/import fields; does not remove constraints or permissions.
New development packages: mutmut, click, libcst, setproctitle, textual, linkify-it-py,
mdit-py-plugins, pyyaml-ft and typing-extensions. Exact versions/licenses in dependency inventory.

- `.dockerignore`, `.gitignore`, `Dockerfile`, `pyproject.toml`, `poetry.lock`.
- `apps/configuration/models.py`, `apps/configuration/validators.py`,
  `apps/configuration/importing.py`,
  `apps/configuration/management/commands/import_campground.py`, configuration migration above.
- `apps/tenancy/management/commands/tenant_command.py`, `apps/reservations/services.py`,
  `apps/campsites/views.py`, `apps/dashboard/forms.py`, `templates/home.html`.
- `data/campgrounds/georgia-mountain-fairgrounds.json`, `scripts/mutation_test.py`,
  `tests/integration/test_campground_import.py`, `tests/integration/test_date_ranges.py`.
- `README.md`, `PROJECT_SPEC.md`, `SECURITY.md`, `docs/georgia-mountain-fairgrounds.md`,
  `docs/mutation-testing.md`, `docs/architecture.md`, `docs/security.md`, `docs/threat-model.md`,
  `docs/security-decisions.md`, `docs/security-findings.md`, `docs/administration.md`,
  `docs/deployment.md`, `docs/backup-and-restore.md`, `docs/incident-response.md`,
  `docs/dependency-inventory.md`, `docs/implementation-progress.md`.

### Remaining work, recommended next steps and unexecuted checks

1. Obtain authoritative site roster/capacities/hookups/seasonal dates/map positions and
   reconcile source counts/monthly price. Review drafts before activation; do not equate
   placeholder values with specifications.
2. Implement/validate monthly stays, seasonal windows and campground-specific deposit,
   cancellation and rate-category behavior before opening online reservations. No pricing
   engine/payment processing or booking-opening web control was added.
3. Expand mutation campaigns to reservation authorization, idempotence and policy logic,
   then authentication/tenant boundaries under separately reviewed targeting. The documented
   broad reservation-service mutation command has **not** been executed.
4. Complete outstanding encrypted backup/restore, SMTP, public ACME renewal, load, frontend
   advisory/manual browser/accessibility and release acceptance work. Earlier unexecuted
   release commands remain unverified. This application is **not production-ready**.

Commands from the repository root after protected local test provisioning:

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/pip-audit --progress-spinner off
poetry check --lock
```

Use the matching Compose project/overlay for deployment checks in `deployment.md` and
`georgia-mountain-fairgrounds.md`. Mutation nonzero results require review, not disabled
checks or altered validation. Preserve the stricter implementation when a conflict arises.

### Final validation disposition

Final rebuilt web image `sha256:90d0672294d5a8787e97aaa2fbec1aa47c3574394bb25dca9853152fa8e0f551`
passed Trivy OS/Python HIGH/CRITICAL scanning with zero findings at those severities.
Source Dockerfile misconfiguration checks and Poetry lock vulnerability checks passed;
the lock was also explicitly scanned with `--include-dev-deps`, with zero HIGH/CRITICAL
findings. Source-only, redacted Gitleaks found no leaks. The final runtime deployment check
reported zero issues and the tenant-scoped migration check reported no model changes.
Both mutation campaigns' disposable databases and temporary secret directories were
confirmed removed. Reviewed mutant source/status artifacts remain private and ignored.

The local validation stack is **stopped**, with all volumes and the provisioned campground
retained; the separate loopback PostgreSQL test service remains available. No public
production service was launched. The local stack can be restarted with its existing
protected development TLS configuration:

```sh
APP_DOMAIN=localhost DJANGO_ALLOWED_HOSTS=localhost APP_UID=501 APP_GID=10001 \
  docker compose -p campground-hardened-validation -f compose.yaml \
  -f /private/tmp/campground-traefik-validation.yaml up -d db web proxy
```

That scratch overlay binds only loopback 18080/18443; it is specific to this validation
workspace, not a portable deployment manifest. Verify/trust the development CA through the
normal local procedure; never bypass certificate verification. Use `deployment.md` for a
new installation. Earlier pre-task Git work and a concurrently created owner checkpoint
were preserved; no Git commit or push was made by this task.

## Docker Hub distribution — 2026-11-24

Current phase: simplified image distribution for isolated evaluation; production acceptance
remains incomplete. Owner requested build/tag/publish to Docker Hub, selected `thecyberbutler`,
and explicitly approved **three public repositories with source visibility** after the
private-repository quota prevented three private repositories. SD-025 records the scope,
risks, alternatives, mitigations and irreversible public-copy limitation. No approval is pending.

### Completed publication and functionality

Published and verified tag **`0.1.0-alpha.20261124-08d15ef2bd0f`** in:

- `docker.io/thecyberbutler/campground-web`
- `docker.io/thecyberbutler/campground-db`
- `docker.io/thecyberbutler/campground-proxy`

All three manifest indexes contain Linux AMD64 and ARM64 images plus minimal build provenance.
Remote index digests match the locally scanned images. Anonymous registry inspection and
anonymous pulls by digest passed for both architectures in all three repositories. The exact
indexes and source snapshot hash are recorded in
`releases/0.1.0-alpha.20261124-08d15ef2bd0f/{manifest.json,images.env,README.md}`.
No latest/stable tag, public application deployment, or production-readiness claim was made.

Added `scripts/release_images.py`: private allowlisted source snapshot, source-content hash
in prerelease tag, two-platform local builds, per-platform security scans, PostgreSQL test/
coverage gates, image ownership/startup probes, credential-helper-only registry auth,
visibility/namespace/tag/digest checks, refusal to overwrite different existing tags, exact
artifact push and remote digest verification. No rebuild occurs during publication. A
nonzero gate blocks publishing; failed/partial publication cannot emit a complete deployment
lock. The script defaults to private repositories; explicit public mode requires the
separately documented owner approval. Existing repository visibility is never silently changed.

Added `compose.registry.yaml`, which removes local build directives and substitutes verified
images for all five services, reusing the web digest for migration/provision jobs. It retains
the base Compose networks, mounts, secret separation, ports, users, capability drops, readonly
filesystems, health/resource limits and controlled migrations. Prebuilt artifacts use fixed
UID/GID 10001; existing differently-owned data/secrets require reviewed migration, not relaxed
permissions/root workarounds. Local source-building deployment remains available.

### Security impacts and findings

Public distribution intentionally exposes packaged source/dependency/build metadata under
SD-025. Anyone may retain downloaded copies; this cannot be undone by deleting a repository.
No camper data, existing accounts, runtime secrets, certificate volumes, Docker credentials,
mutation artifacts or owner editor files were included in build contexts or published images.
No runtime authentication/authorization/database/container control was weakened. Docker Hub
is a distribution dependency only; self-hosted application operation is unchanged.

The first private build snapshot produced root-owned unreadable application files inside
local candidates. Image execution checks caught this before publication. Corrected ordinary
source modes under the still-private parent workspace, added a regression, rebuilt and
validated both platforms; no privileges or secret permissions were expanded. Failed initial
candidates were not published. The publishing token could not change visibility; after the owner's follow-up, public
visibility was verified. No broader token permissions were requested by this task. No existing
repository/image content was deleted by this task.

No new known application vulnerability was identified. The packaging defect is resolved;
external-source credential publication and earlier release limitations remain as previously
recorded. Scanners and digest verification do not establish independent publisher signatures,
complete toolchain assurance or production readiness.

### Validation actually executed

- Release snapshot: **153 PostgreSQL tests passed** with the **85% coverage gate passed**, both
  during build and immediately before publishing. A full working-repository run measured
  **92.35%** coverage with 153 tests. Existing independent-connection concurrency/security
  tests remain included; PostgreSQL was restarted for these tests, never replaced by SQLite.
- Final targeted publishing regression suite: **12 passed**, including three added post-build
  negative tests for visibility mismatch and refusal to overwrite an existing different digest.
  Other cases cover registry/name/tag/platform/manifest validation, omitted secrets, symlinks,
  HTTP redirect/TLS/error-output controls, readable snapshot modes under a private parent,
  and an actual Compose merge comparison preserving every unrelated security setting.
- Ruff lint/format and Bandit passed on source snapshots and final changes. Narrow B404/B603/
  B108 reviewed annotations are documented in SD-025; no broad scanner rule was disabled.
- Redacted Gitleaks source scans passed. Trivy source/Poetry lock (including dev dependencies)
  and Dockerfile HIGH/CRITICAL scans passed. Every image/architecture passed HIGH/CRITICAL
  vulnerability scanning and a separate secret scan without a severity filter, before build
  completion and again immediately before publication. No findings were waived/suppressed.
- Both architecture variants execute as 10001:10001 with expected directory ownership;
  web imports required libraries; web/proxy refuse missing required secrets/TLS configuration.
  Database binary/version and non-root directory ownership checked. This is **not** a fresh
  full database initialization/HTTPS lifecycle test of the published UID-10001 stack.
- Published digest lock rendered with real Docker Compose: no builds remain, all five services
  retain readonly/cap-drop/no-new-privileges, and web/database ports remain unpublished.
- All remote index digests and anonymous AMD64/ARM64 pulls verified. No registry credential
  material was printed, persisted in release artifacts, or passed as a build argument.

### Files, migrations and dependencies

New: `compose.registry.yaml`, `scripts/release_images.py`,
`tests/security/test_release_images.py`, `docs/container-publishing.md`, and the three
non-secret release metadata files listed above.

Updated in this task: `README.md`, `PROJECT_SPEC.md`, `SECURITY.md`,
`docs/architecture.md`, `docs/deployment.md`, `docs/security.md`, `docs/threat-model.md`,
`docs/security-decisions.md`, `docs/security-findings.md`, `docs/dependency-inventory.md`,
`docs/backup-and-restore.md`, `docs/incident-response.md`, `docs/implementation-progress.md`.
Earlier uncommitted work and owner editor settings were preserved. No Git commit/push was made.

No database migration, Python/runtime dependency, base-image change or new application
service was introduced. Host tooling reuses existing Docker/Buildx, Requests, Trivy/Gitleaks
and the Poetry test environment. All three Dockerfiles retain their existing security settings.

### Repeatable commands and remaining work

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/python scripts/release_images.py build --namespace thecyberbutler --version 0.1.0-alpha.20261124
# Substitute the completed build's actual manifest path; public mode uses SD-025 approval.
.venv/bin/python scripts/release_images.py publish .runtime/releases/candidate-EXAMPLE/manifest.json --public-approved
# After configuring non-secret .env and a dedicated UID/GID-10001 deployment:
docker compose --env-file .env --env-file releases/0.1.0-alpha.20261124-08d15ef2bd0f/images.env -f compose.yaml -f compose.registry.yaml --profile tools pull
```

Next: rehearse a fresh UID-10001 deployment with protected synthetic secrets and full tenant
initialization/verified HTTPS; complete encrypted restore, ACME renewal, SMTP, load, manual
security/accessibility and remaining application acceptance gates before production. No live
application was deployed from Docker Hub in this task. Registry-side immutable-tag policy,
independent artifact signing, full builder-toolchain/SBOM/distribution-license review and
an approved CI environment remain further release assurance work; none is claimed verified.
Do not bypass those reviews or reopen booking merely because images are easy to pull.

Final source-only Gitleaks scan, including release metadata and new documentation, passed
with no leaks found. The synthetic PostgreSQL test container was stopped again after tests,
restoring its observed pre-validation state; all database volumes are retained. Start the
existing isolated test service (`docker start campground-test-db-hardened`) before repeating
tests on this workstation, or follow README's protected test provisioning on a new host.
The existing application validation stack remains stopped. No production service was started.

## Current task: test banner and AWS development deployment — 2026-11-24

Banner implementation covers directory, tenant, auth/MFA and generic application errors,
with a shared local CSS red banner and server-only validated environment label. HTMX fragments
reuse the containing document. JSON/streams are preserved. Production security settings are
unchanged. Full initial PostgreSQL suite passed **195 tests, 92.71% coverage**; a subsequent
malformed-proxy-path regression was added and is awaiting the next release-snapshot run.
Ruff lint/format and Bandit passed before that final small addition; final checks follow.

Read-only SSH preflight was disclosed verbatim and executed with strict known-host checking.
Target is Amazon Linux 2023/x86_64 with ~4 GB RAM, ~50 GB free storage, passwordless sudo,
no Docker, no deployment path/UID conflicts and no 80/443 listeners. No remote changes were
made during preflight. Fresh-host installation script and secret-safe external HTTPS checker
are prepared. New banner-enabled images are being built/scanned; deployment is not yet verified.

Security decisions: SD-026. No new pending security approval, dependency or database migration.
Only this explicitly requested public development deployment is authorized; production gates
remain outstanding. Existing work and owner editor settings are preserved.

Final banner release `0.1.0-alpha.20261124-935cbb3b3a29` is published in all three approved
public repositories; remote digests match scanned indexes. Build and pre-publish runs each
passed **196 PostgreSQL tests**, including security/concurrency regressions, with **92.97%**
coverage and the 85% gate. Ruff/Bandit, source/documentation Gitleaks, Trivy source/lock/
Dockerfile HIGH/CRITICAL checks, per-architecture image vulnerability and separate secret
scans, and both-architecture non-root/missing-secret startup checks passed. Earlier candidate
6e753d27475b was not published after the final early-proxy error regression was added.

The complete remote transcript is in `docs/aws-test-deployment-transcript.md`, disclosed
before remote mutations. Bundle checksums and publisher digest lock were compared before
upload. Execution has started; final remote/live validation results follow below.

### Completed AWS outcome

The owner-requested development site is live at **https://camp-butts-test.thecyberbutler.io**;
Georgia Mountain Fairgrounds is at `/c/georgia-mountain-fairgrounds/`. Installation and all
reported validation commands completed successfully. This is a **development deployment,
not a production-ready release**. Application login credentials were not created.

- Published release: `0.1.0-alpha.20261124-935cbb3b3a29`; image references are digest-locked in
  `releases/0.1.0-alpha.20261124-935cbb3b3a29/images.env` and the exact remote transcript.
- AWS project/path: `camp-butts-test`, `/opt/camp-butts-test`. Docker 25.0.18 (Amazon package),
  host Python 3.9.25 (Amazon package), verified official Compose 5.8.0. Application Python
  remains 3.13. The 4-GB host has not been load-qualified for production.
- DB/web health checks passed; Django `check --deploy --fail-level WARNING` passed. Runtime
  database probes denied protected DDL, migration/operator data access and audit alteration.
- Public HTTPS/initial ACME issuance verified with trusted certificate validation. Banner
  verified once per directory/home/login/signup/campsites/404 page and on CSRF rejection;
  red CSS/local Bootstrap/HTMX assets served. HTTP redirect, CSP/HSTS/nosniff/private caching,
  CSRF, request-size bound, spoofed forwarding headers, unknown host/SNI and private-resource
  rejection passed. Proxy-generated transport/413 pages are outside Django banner rendering.
- All three actual containers run as 10001:10001, read-only root filesystems, ALL capabilities
  dropped and no-new-privileges. DB/web publish no ports; only Traefik publishes 80/443.
- Secret-directory mode 0700 and six file modes 0600/owner 10001:10001 verified by metadata
  only; secret values were never printed or copied from the workstation.
- Live application confirms development label, DEBUG false, secure session/CSRF cookies,
  **216 inactive draft sites, booking closed, public availability off and zero user accounts**.
- Fresh volumes were initialized; no production data migrated. No schema migration was
  introduced by this task. Existing migrations were applied to the new tenant database.
- No new runtime/frontend dependency, weakened control, pending security approval or newly
  identified exploitable application vulnerability. Visual labeling/error coverage improved;
  this is not a claim to have resolved a previously identified exploit. SD-025's existing public
  image visibility approval still applies; SD-026 records this separately authorized test host.

### Files changed in this task

Application/configuration:
`.env.example`, `compose.yaml`, `compose.dev.yaml`, `config/environment.py`, `config/errors.py`,
`config/middleware.py`, `config/urls.py`, `config/settings/base.py`,
`config/settings/development.py`, `config/settings/testing.py`, `apps/tenancy/middleware.py`,
`templates/layouts/document.html`, `templates/components/test_instance_banner.html`,
`templates/error.html`, `templates/base.html`, `templates/tenancy/directory.html`,
`static/css/app.css`, `tests/security/test_environment_banner.py`.

Operator tools:
`scripts/aws_preflight.sh`, `scripts/deploy_aws_test.sh`, `scripts/check_public_test.py`.
Private local staging/verification artifacts under ignored `.runtime/` contain no transferred
secrets. The transcript preserves their exact contents; existing publishing tools were reused.

Documentation:
`README.md`, `PROJECT_SPEC.md`, `SECURITY.md`, `docs/architecture.md`, `docs/deployment.md`,
`docs/administration.md`, `docs/backup-and-restore.md`, `docs/security.md`,
`docs/threat-model.md`, `docs/security-decisions.md`, `docs/incident-response.md`,
`docs/dependency-inventory.md`, `docs/security-findings.md`, `docs/implementation-progress.md`,
`docs/aws-test-deployment-transcript.md`.

Release metadata:
`releases/0.1.0-alpha.20261124-935cbb3b3a29/README.md`, `manifest.json`, `images.env`.
All earlier uncommitted work and owner editor settings are retained. No Git commit/push.

### Repeatable validation and remaining work

```sh
# Start only the existing isolated synthetic PostgreSQL service before local tests:
docker start campground-test-db-hardened
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
bash -n scripts/aws_preflight.sh scripts/deploy_aws_test.sh
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
```

The transcript supplies exact executed remote Django/database/state/container validation
commands. Do **not** rerun the fresh-install script on the installed host. Re-running public
checks makes bounded synthetic requests, including CSRF/request-size negative cases, with
no successful login or reservation creation.

Still unverified/not executed in this task: public ACME **renewal**, expiry alerts, encrypted
backup/restore (including tenant directory), host storage encryption/AWS security-group and
IAM review, whole-host security update review, load/capacity testing, SMTP delivery,
manual browser/accessibility/security review, and the remaining application/release gates.
The previous mutmut campaign was not rerun for this presentation/deployment change; no
mutation-score improvement is claimed. Standalone pip-audit was not rerun; current Trivy
Poetry-lock scans included development dependencies. Existing external-source credential
publication remains recorded separately; no source credential was imported or reproduced.

Recommended next steps: use synthetic data; create an operator account via the protected
interactive onboarding procedure and enroll MFA; verify host encryption/management access,
recovery and certificate monitoring; review campground roster/rate conflicts before opening
inventory; complete outstanding acceptance/security gates before production or real data.

Final source/documentation/release-metadata Gitleaks scan passed. The local synthetic test
PostgreSQL container was stopped after validation, restoring its observed pre-task state;
all volumes are retained. The AWS development deployment remains running.

## Current task: Google sign-in — 2026-11-24

Read AGENTS.md, the complete specification, architecture/security/threat/decision/progress
records before modification. Initial tree clean except owner editor settings. Owner requested
Google OAuth, supplied an External test client, installed its protected server-side file,
and explicitly approved restricted Google-only egress (SD-027). No credentials read/printed.

Implementing optional per-campground allauth Google code flow, PKCE/nonce/signed-token checks,
no email auto-linking/token storage, protected connection management and approval-preserving
signup. Local-only operation remains the default without a protected credential file. The
web stays internal; optional non-root Squid sidecar supplies the approved two-host TLS tunnel.
No CSP/TLS/MFA or existing auth control is relaxed. Tests, scanner gates, deployment transcript
and in-place test upgrade are pending. Initial 40 existing banner tests passed; installed
pip-audit found no known vulnerabilities after allauth socialaccount extras were enabled.

### Google implementation and local validation — 2026-11-25

Implemented optional per-tenant Google code flow, protected credential parser, strict OIDC
verification, PKCE/nonce, concurrent single-use callback state, approval-preserving signup,
explicit password/MFA-protected linking/unlinking and session revocation. No provider tokens
are stored; runtime cannot read SocialApp credentials or create/update SocialToken rows.
Django's unlink cascade needs SELECT/DELETE on SocialToken, retained under forced tenant RLS.
Added optional hardened Squid overlay, both-architecture release gates, real proxy boundary
checks, encrypted pre-upgrade snapshot helper and fail-closed first-enable AWS upgrade.

235 tests passed, 92.53% application/config coverage, including new OAuth callback concurrency,
unlink assurance and encrypted snapshot tests. The isolated release gate also passed all 235
tests with its restrictive umask after correcting a negative test's directory-mode setup.
Ruff/format/Bandit and shell syntax checks passed. Initial installed pip-audit and real proxy
allow/deny checks passed. Final release scans/publication and remote deployment remain pending.
Vendor allauth socialaccount migrations 0001–0006 are required per tenant; no custom model
migration is introduced. OAuthlib 4.0.1/PyJWT 2.15.1 and existing Requests transitives enter
runtime via allauth's socialaccount extra; Squid is a scoped approved infrastructure addition.
No new pending security exception. Google provider dependence and permitted-host egress abuse
remain approved residual risks; live consent/token exchange, encrypted restore, off-host
recovery and existing production release gates remain unverified.

### Published and deployed result

Published and deployed `0.1.0-alpha.20261125-3386d5caf5b3` to the existing AWS test instance.
Release metadata is in `releases/0.1.0-alpha.20261125-3386d5caf5b3/`; remote manifest digests
were verified before deployment. AMD64 database/Traefik filesystem layers are identical to
the previous release. No application database reset, production data import, default account,
automatic approval or privilege promotion was performed. No secret values were printed or
transferred in the bundle. The owner-supplied Google credential file remains protected.

The exact SSH/SCP scripts, file contents and one additional disclosed read-only status check
are recorded in `aws-google-deployment-transcript.md`. Before migration, web writes stopped
and a bounded full-database dump was streamed directly to Fernet encryption. Authenticated
decryption was verified; no plaintext dump file was written. This does not prove PostgreSQL
restore or complete disaster recovery. The key and ciphertext are separately protected on
the same host; off-host escrow/complete recovery remain pending.

Completed remote validation:
- All four services running; web, DB and Google egress report healthy.
- Django deployment checks pass with DEBUG false, development banner and secure cookies.
- Actual runtime DB role denies schema/admin/audit mutation, SocialApp credential reads and
  token INSERT/UPDATE; forced RLS protects new social-account tables.
- Synthetic SocialAccount create/delete succeeds under the real runtime role and is rolled
  back; no test user/link is retained.
- Google signing-key HTTPS succeeds through the restricted proxy with TLS verification.
- Actual non-root/read-only/capability/no-new-privileges, private networks, secret-mount
  scope and sole public Traefik port boundaries pass.
- Public HTTPS/banner/static/security headers, CSRF, host/SNI and body limits pass.
- Public Google button, CSRF-protected start, fixed tenant callback/client/scope, PKCE/nonce,
  invalid state rejection and disabled browser-token endpoint pass.

The owner was asked to complete a real Google test login. Until that outcome is recorded,
human consent, real authorization-code exchange and successful approved-user sign-in remain
**unverified**. Google remains External/Testing with the owner-configured test audience.
Campground approval and explicit local-account linking requirements remain in effect.

No new unresolved applicable HIGH/CRITICAL dependency/image finding was reported by the scans.
Draft cascade-permission, mapped-address ACL and test-fixture defects were corrected before
deployment; these are not claims of remediating a previously deployed exploit. The existing
upstream-published network credential finding remains unresolved externally. SD-027 records
the approved external identity/limited egress risk; no further security approval is pending.

### Modified files in the Google task

- `.dockerignore`
- `.env.example`
- `AGENTS.md`
- `Dockerfile.google-egress`
- `PROJECT_SPEC.md`
- `README.md`
- `SECURITY.md`
- `apps/accounts/signals.py`
- `apps/configuration/context.py`
- `apps/google_auth/__init__.py`
- `apps/google_auth/adapter.py`
- `apps/google_auth/provider.py`
- `apps/google_auth/transport.py`
- `apps/google_auth/urls.py`
- `apps/google_auth/views.py`
- `compose.google.yaml`
- `config/google.py`
- `config/settings/base.py`
- `config/urls.py`
- `docs/administration.md`
- `docs/architecture.md`
- `docs/aws-google-deployment-transcript.md`
- `docs/backup-and-restore.md`
- `docs/container-publishing.md`
- `docs/dependency-inventory.md`
- `docs/deployment.md`
- `docs/google-oauth.md`
- `docs/implementation-progress.md`
- `docs/incident-response.md`
- `docs/security-decisions.md`
- `docs/security-findings.md`
- `docs/security.md`
- `docs/threat-model.md`
- `infra/google-egress/squid.conf`
- `poetry.lock`
- `pyproject.toml`
- `releases/0.1.0-alpha.20261125-3386d5caf5b3/README.md`
- `releases/0.1.0-alpha.20261125-3386d5caf5b3/images.env`
- `releases/0.1.0-alpha.20261125-3386d5caf5b3/manifest.json`
- `scripts/check_database_boundary.py`
- `scripts/check_google_egress.py`
- `scripts/check_public_google.py`
- `scripts/encrypt_deployment_snapshot.py`
- `scripts/release_images.py`
- `scripts/tenant_database.py`
- `scripts/upgrade_aws_google.sh`
- `static/js/google-redirect.js`
- `templates/base.html`
- `templates/google_auth/redirect.html`
- `templates/socialaccount/connections.html`
- `templates/socialaccount/snippets/login.html`
- `templates/socialaccount/snippets/provider_list.html`
- `tests/security/test_deployment_snapshot.py`
- `tests/security/test_google_oauth.py`
- `tests/security/test_release_images.py`

No custom database migration was added; allauth socialaccount migrations 0001–0006 were
applied to the sole deployed campground. Runtime dependencies: OAuthlib/PyJWT and existing
Requests transitives via the socialaccount extra; optional infrastructure: Squid. The
mandatory stack remains in place. Owner editor settings were left untouched. No Git commit/push.

### Repeat validation and outstanding checks

```sh
docker start campground-test-db-hardened
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
bash -n scripts/upgrade_aws_google.sh
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
docker stop campground-test-db-hardened
```

The final release build and publish commands each ran source Gitleaks, Trivy source/dependency
and both-architecture vulnerability/secret scans, 235 PostgreSQL tests, non-root startup
checks and real proxy network checks. See `google-oauth.md` and `container-publishing.md` for
repeatable image/network gates; do not run the disposable proxy test on the enabled server's
in-use subnet. The first-enable upgrade script must not be rerun on this installed host.

Not executed/verified: interactive real Google completion, a new mutmut campaign, full
PostgreSQL encrypted restore/off-host key recovery, certificate renewal/alerts, host storage
encryption/security-group/IAM review, broader host vulnerability/license/builder review,
SMTP delivery, load/capacity tests and remaining production acceptance/security gates.
For a separate bounded synthetic mutation run after starting its test DB:
`.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900`. This existing
reservation mutation command does not constitute OAuth mutation coverage.

Recommended next steps: complete owner Google acceptance and normal account approval/linking;
then finish encrypted recovery and operational review before real camper data or production.
The application remains a development prerelease. Local synthetic PostgreSQL was stopped
after validation with all volumes retained; the AWS test deployment remains running.

## Repository hygiene — 2026-11-25

Added an ignore rule for the owner’s local editor settings and removed references to its
specific directory from tracked documentation. The directory had no tracked files; existing
local settings were preserved. Git index/ignore checks and whitespace validation passed.
No runtime, dependency, database, security-control or deployment change. No vulnerability
or security exception introduced; no approval pending. This maintenance change is kept in
a focused commit, separate from the requested workflow instruction and visual redesign.

## Feature commit workflow — 2026-11-25

Recorded the owner's request in AGENTS.md: commit each completed, validated feature with
its tests/documentation and keep unrelated work separate. Secret exclusions and security
gates remain mandatory. Reviewed the instruction diff and Git whitespace; no runtime change,
dependency, migration, vulnerability or pending approval. No remote push is part of this task.

## Interface modernization — 2026-11-25

Current phase: presentation refinement, completed locally; development prerelease and all
existing production security gates remain in force. Repository hygiene and commit workflow
were committed separately as `74e7d7c` and `0427eee`.

### Completed functionality and decisions

Added a shared forest-green/warm-neutral design with rounded panels, softer shadows,
responsive navigation, short hover/color transitions, accessible focus and reduced-motion
support. Updated campground home/directory, login and account layouts, campsite search,
reservations, camper dashboard, operations/tables and errors. Long reference information
uses native disclosures; the booking-closure notice remains outside them. Locally authored
decorative artwork gives the pages a consistent identity without external assets or scripts.
The red development/test banner remains unchanged in wording and color.

Architecture remains server-rendered Django with the existing Bootstrap/HTMX stack and
local CSS/system fonts. No dependency, migration, Python application logic, permission,
tenant boundary, database policy, CSRF, CSP, OAuth or MFA control changed. SD-028 records the
presentation decision and residual compatibility risks. No security reduction or pending
approval; no new vulnerability identified or existing vulnerability declared resolved.
Existing findings and release gates remain open as previously documented.

### Files modified or added for the design

- `static/css/app.css`, `static/images/camp-landscape.svg`.
- `templates/base.html`, `templates/components/brand_mark.html`, `templates/home.html`,
  `templates/tenancy/directory.html`, `templates/error.html`, `templates/pagination.html`.
- `templates/allauth/layouts/base.html`, `templates/allauth/elements/button.html`,
  `templates/accounts/registration_received.html`, `templates/google_auth/redirect.html`,
  `templates/socialaccount/connections.html`.
- `templates/campsites/list.html`, `templates/campsites/results.html`,
  `templates/campsites/detail.html`, `templates/reservations/form.html`,
  `templates/reservations/detail.html`, `templates/dashboard.html`.
- `templates/dashboard/operations.html`, `templates/dashboard/audit.html`,
  `templates/dashboard/calendar.html`, `templates/dashboard/export.html`.
- `README.md`, `PROJECT_SPEC.md`, `docs/interface-design.md`, `docs/architecture.md`,
  `docs/dependency-inventory.md`, `docs/security.md`, `docs/security-decisions.md`,
  `docs/threat-model.md`, `docs/implementation-progress.md`.

### Validation

- Existing PostgreSQL suite: **235 passed**, including authentication, MFA, Google,
  authorization, tenant isolation, CSRF, banner, occupancy and concurrency regressions.
  Final rerun also included one private synthetic preview-generation case: **236 passed**,
  **92.53% coverage**. No tests or security controls weakened or skipped.
- Chromium: **39 page/viewport checks** across 13 synthetic pages at 1440, 390 and 320 pixels.
  Verified no horizontal overflow, loaded local assets, form labels and test banner;
  keyboard account disclosure, visible focus and reduced-motion behavior also passed.
  Reviewed desktop home/login/operations and mobile home screenshots. Browser rendering
  used sanitized responses with hidden form secrets removed and blocked network requests;
  it is not an end-to-end OAuth or screen-reader test.
- Eight primary text/background palette pairs meet 4.5:1 contrast. Fixed SVG assets checked
  for geometry-only content without external references, event handlers or scripts.
- Ruff lint/format, Bandit and Git whitespace checks passed.
- Final Gitleaks source scan and Trivy source/dependency/configuration scan passed
  (including development dependencies; HIGH/CRITICAL blocking severity). The scan used
  an isolated nonignored-file copy, excluding secrets and local runtime artifacts.

Repeat the repository checks with the existing protected local test database configuration:

```sh
docker start campground-test-db-hardened
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
git diff --check
docker stop campground-test-db-hardened
```

Private sanitized preview artifacts are in the ignored `.runtime/ui-review/` directory;
they are not application fixtures or committed tests. See `interface-design.md` for the
browser review checklist. No new mutation campaign, pip-audit, container build/image scan,
deployment check on AWS, interactive Google acceptance, additional browser-engine or
screen-reader acceptance was performed for this presentation-only change. Repeat image
and dependency release gates before publishing, as documented in `container-publishing.md`;
the bounded mutation command remains
`.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900` with its synthetic DB running.

No images published, remote push or AWS deployment performed. Next: review the visual design,
complete wider accessibility/browser acceptance, then build and scan a new release before
updating the test deployment with the required exact remote transcript. Existing production
recovery, operational review and Google human acceptance work remain outstanding.
The isolated review browser and synthetic test database were stopped after validation;
existing database volumes and private sanitized screenshots were retained.

## Scanned interface release and test deployment — 2026-11-25

The owner reviewed the design and requested “lets scan and deploy”. Scope: the existing
public AWS development instance, retaining production Django security settings and the
red test banner. No production promotion, dependency, schema, credential, grant or network
change is authorized or needed. The existing SD-025/026/027 scopes remain unchanged.

Release `0.1.0-alpha.20261125-5815b9993895` was built and published to the approved public
repositories; each remote manifest digest was independently verified. Source snapshot
`5815b99938950eb13960fd456a2c809f3725f6b61d39bc4230c490875ad08a60` includes the committed
interface feature `f562aba`. Both build and publication passed 235 PostgreSQL tests, the
85% coverage gate, Ruff/format/Bandit, Gitleaks, Trivy source/lock/configuration and all
four images' AMD64/ARM64 vulnerability/secret gates. Non-root/fail-closed startup checks
and the disposable Google restricted-egress checks passed on both release invocations.
Poetry lock validation passed with existing metadata deprecation warnings; pip-audit found
no known vulnerabilities. The initially attempted `.venv/bin/poetry` path was absent; the
installed `poetry` command completed the check successfully. No check was bypassed.

The two releases have identical DB/proxy/egress filesystem layers on both architectures;
image runtime configurations differ only in release labels. No database migration is
introduced. A strict-host-key SSH preflight, disclosed before connecting, confirmed the
expected live release, unchanged Compose checksums, healthy services and adequate disk.
The complete upgrade transcript and transferred contents were provided before execution;
the deployment bundle passed Gitleaks and shell/Python syntax checks.

Deployment completed successfully. The baseline/configuration checks matched; model and
migration consistency checks passed without schema/grant changes. Web was stopped for a
bounded, directly encrypted DB snapshot; authenticated decryption was verified. Previous
images, snapshots, all data/TLS volumes and protected secrets were preserved. The new image
lock was installed, assets collected and services recreated. No rollback was needed.

All four services are running, with web/DB/egress healthy. Actual image identities, non-root/
read-only/capability/network/public-port boundaries, Django deployment checks, denied runtime
DB operations/forced social-account RLS, closed booking/inactive inventory and Google TLS
passed. Public HTTPS, red banner, local assets, headers, CSRF, host/SNI/body-size boundaries,
Google start/PKCE/nonce/invalid-callback/disabled-token-route and exact CSS/artwork hash checks
passed. No real user consent/token exchange was performed or claimed. The local synthetic
PostgreSQL container was stopped with its volume retained. No Git remote push was performed.

Files added/updated: `README.md`, `docs/implementation-progress.md`, `docs/security-decisions.md`,
`docs/security-findings.md`, `docs/interface-design.md`, `docs/deployment.md`,
`docs/backup-and-restore.md`, `docs/container-publishing.md`, `docs/aws-ui-deployment-transcript.md`,
and `releases/0.1.0-alpha.20261125-5815b9993895/{README.md,manifest.json,images.env}`.
Private transfer/probe files remain in ignored `.runtime/`; no application source changed
in this deployment task. No dependencies or migrations added. No security regression or
new vulnerability identified by the executed checks; no vulnerability newly resolved, no
suppression/waiver and no pending security approval for this release. Existing findings,
shared-host/provider residual risks and unfinished production gates remain.

### Executed validation and release commands

```sh
poetry check --lock
.venv/bin/pip-audit --progress-spinner off
docker start campground-test-db-hardened
TEST_DATABASE_PORT=55433 .venv/bin/python scripts/release_images.py build --namespace thecyberbutler --version 0.1.0-alpha.20261125
SSL_CERT_FILE=/etc/ssl/cert.pem TEST_DATABASE_PORT=55433 .venv/bin/python scripts/release_images.py publish .runtime/releases/candidate-morlqouq/manifest.json --public-approved
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
.venv/bin/python .runtime/aws-ui-upgrade-5815b9993895/check_public_ui.py
docker stop campground-test-db-hardened
git diff --check
```

The build/publish commands each execute Ruff/format, Bandit, PostgreSQL tests/coverage,
Gitleaks, Trivy and image/egress checks; see the release guide for their full gates. Build
creates a new private candidate path; do not assume its name or overwrite an existing tag.
Exact remote commands, transferred scripts, digest lock, snapshot and rollback behavior are
recorded in `aws-ui-deployment-transcript.md`; do not rerun its completed one-time upgrade.

Remaining/unexecuted: a new mutmut campaign, interactive Google login, broader browser and
screen-reader acceptance, full encrypted/off-host recovery, certificate renewal/alerts,
AWS storage/firewall/IAM review, SMTP delivery, capacity tests and production acceptance.
The optional bounded mutation command remains
`.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900` with its synthetic DB
running. Host-local authenticated snapshot decryption is not a complete restore rehearsal.
Recommended next steps: review the live UI, complete human Google acceptance and recovery/
operational review, then satisfy all production release gates before accepting real camper data.

## Email-only accounts — 2026-11-25

Owner requested no usernames and email-only identification. Implemented local account model,
manager, signup/login, staff displays, Google lockout lookup and operator-command changes;
case-insensitive email uniqueness remains per campground, UUIDs and permissions unchanged.
Migration `accounts.0003_email_identity` validates legacy email, retires sessions and carries
recent username failure counts into email lockouts before removing the obsolete column.
No new dependency, account merge, email attestation, MFA bypass or weaker control. Google
profile/phone expansion is explicitly approved in SD-029 and is a separate feature below.

Targeted PostgreSQL email/migration/tenant/workflow checks: 31 passed. Full suite/scans are
pending completion. Initial tenant test failures were obsolete hardcoded username logins;
updated those inputs to email while retaining isolation assertions. Existing concurrency
teardown reported live test connections once; a subsequent isolated run completed normally.
No failure was suppressed or claimed passed. No live deployment or image publication performed.
See `email-identity.md` for irreversible migration, backup, stopped-writer and rollback limits.

Email feature validation completed: full PostgreSQL suite **242 passed, 92.29% coverage**;
then **10 targeted migration/concurrency checks passed**, including two added legacy-data
refusal cases and a simultaneous case-variant signup case. Corrected the new test module's
name collision and expected completion URL before the successful run. Ruff lint/format,
Bandit, Gitleaks and Trivy source/dependency/configuration gates passed. No dependency/image
build, new mutation campaign or live schema migration is claimed by this feature commit.

Files: account manager/model/forms/adapters/security/operator commands and migration 0003;
Google adapter/signup username compatibility; base settings; staff views/templates; existing
account/Google/tenant/workflow/invitation tests and new email identity/migration/concurrency
tests; PROJECT_SPEC, README, administration/architecture/deployment/security/threat-model/
decision/progress docs and the new `docs/email-identity.md`. Existing mandatory controls
remain. No new vulnerability identified, prior vulnerability declared resolved or security
approval pending for email identity; approved Google profile work follows separately.

Repeat with the protected synthetic PostgreSQL running:
`TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85`.
The targeted commands use `tests/security/test_email_identity.py` and
`tests/concurrency/test_email_registration.py`. Deployment requires migration review and a
new scanned release; the running AWS test instance is unchanged.

## Google name and optional phone prefilling — 2026-11-25

Owner explicitly approved profile/phone scopes and restricted People API access after risk,
control, alternative and rollback disclosure (SD-029). Implemented with the existing stack;
no new dependency/migration is added by this feature. Email-only identity is separately
committed as `47bc241` with `accounts.0003_email_identity`.

New Google registration prefills bounded first/last names from verified ID-token claims and
an optional primary/first usable phone from the fixed People self-profile endpoint. Fields
remain editable; rules/policies are not preaccepted. Missing/denied/malformed phone or optional
profile TLS failure leaves manual input without weakening authentication/TLS. Existing accounts
and explicit linking do not fetch phones or overwrite local details. No contact-list access,
unrelated profile fields, persistent tokens, phone verification/authentication/recovery or
automatic email linking. Profile suggestions are transient in the existing encrypted signup
session and only confirmed contact fields enter the account record.

The existing private non-root proxy gains only `people.googleapis.com:443`. Application
transport fixes GET/URL/query fields/sources and denies query overrides, redirects and excess
response size. Actual proxy TLS, wrong-peer/host/port/method, private/metadata (including mapped
IPv6), DNS-to-metadata and direct-egress denial passed with the changed configuration. Both
AMD64/ARM64 proxy images passed vulnerability/secret scans, non-root execution and config parsing.
Local review tag: `campground-google-egress:profile-review`; not published or deployed.

Validation: the complete PostgreSQL suite **271 passed, 92.74% coverage**, including new signed
callback/profile/permission/fallback/escaping/non-overwrite/transport tests and email migration,
concurrent signup, callback replay, tenant isolation, MFA and reservation concurrency regressions.
The callback test's worker cleanup now closes each thread's DB connections, resolving the
observed synthetic-test teardown warning; the final full run had no such warning. No test or
security check was weakened or skipped. Ruff/format and Bandit passed before the final full run;
final scans/documentation checks follow below.

Google operator setup: enable People API in the existing test OAuth client's project; retain
OpenID/email scopes and add profile (`userinfo.profile` in Data Access) plus
`https://www.googleapis.com/auth/user.phonenumbers.read`. Keep Testing audience/test users;
review any Google production verification requirements. Client ID/secret/callback and
JavaScript origins need no changes. Never send credentials or callback tokens in chat.
Detailed setup and exact callback remain in `google-oauth.md`.

Files: `apps/google_auth/{constants,profile,provider,transport,adapter,views}.py`,
`config/settings/base.py`, `infra/google-egress/squid.conf`, `scripts/check_google_egress.py`,
`scripts/check_public_google.py`, `tests/security/test_google_oauth.py`, AGENTS/PROJECT_SPEC/
README and architecture/security/threat-model/deployment/Google/dependency/backup/progress docs.
Security impact is the specifically approved broader Google data/egress boundary; no other
exception or pending security approval. No vulnerability identified or newly declared resolved;
remaining prior findings/production gates are unchanged.

No AWS connection, image publication or deployment in this implementation task. The running
interface prerelease `0.1.0-alpha.20261125-5815b9993895` still uses the previous username schema
and Google scopes. Do not run the new public scope probe against it and claim a regression.
Next: owner Google Cloud configuration, a new fully scanned release, encrypted backup and
stopped-writer migration per campground with exact transcript disclosure; then human Google
consent/profile/approved-login acceptance. Do not reuse the UI-only old-image rollback script.
A new mutation campaign, live profile retrieval, cross-browser/screen-reader testing, full
off-host restore and existing production acceptance work remain unexecuted/unverified.

Final checks passed: Ruff lint/format, Bandit, Gitleaks source/documentation, Trivy
source/dependency/configuration and pip-audit. The secret scanner initially flagged a public
OAuth scope string in a synthetic test; reviewed it as a false positive, clarified the test
expression and reran the case and scans without suppressing rules. See security-findings.md.
The targeted rerun passed. No actual secret disclosure or vulnerability is claimed.

Repeat commands (synthetic database only; image reference is a local reviewed test build):

```sh
docker start campground-test-db-hardened
TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
.venv/bin/ruff check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/ruff format --check apps config scripts tests manage.py gunicorn.conf.py
.venv/bin/bandit -r apps config scripts manage.py gunicorn.conf.py -q
.venv/bin/pip-audit --progress-spinner off
.venv/bin/python -m scripts.check_google_egress campground-google-egress:profile-review
docker stop campground-test-db-hardened
```

The isolated proxy validation used the release helper's allowlisted snapshot, multi-platform
build, per-platform Trivy scans and non-root smoke/network checks. No existing deployment
network or secret was mounted. A complete published release remains outstanding; run the
normal build/publish gates and prepare a schema-aware transcript before updating AWS.

Complete file inventory for the two requested account/profile features:

- `AGENTS.md`
- `PROJECT_SPEC.md`
- `README.md`
- `apps/accounts/adapters.py`
- `apps/accounts/forms.py`
- `apps/accounts/management/commands/authorize_account.py`
- `apps/accounts/management/commands/create_invitation.py`
- `apps/accounts/managers.py`
- `apps/accounts/migrations/0003_email_identity.py`
- `apps/accounts/models.py`
- `apps/accounts/security.py`
- `apps/dashboard/views.py`
- `apps/google_auth/adapter.py`
- `apps/google_auth/constants.py`
- `apps/google_auth/profile.py`
- `apps/google_auth/provider.py`
- `apps/google_auth/transport.py`
- `apps/google_auth/views.py`
- `config/settings/base.py`
- `docs/administration.md`
- `docs/architecture.md`
- `docs/backup-and-restore.md`
- `docs/dependency-inventory.md`
- `docs/deployment.md`
- `docs/email-identity.md`
- `docs/google-oauth.md`
- `docs/implementation-progress.md`
- `docs/security-decisions.md`
- `docs/security-findings.md`
- `docs/security.md`
- `docs/threat-model.md`
- `infra/google-egress/squid.conf`
- `scripts/check_google_egress.py`
- `scripts/check_public_google.py`
- `templates/dashboard/accounts.html`
- `templates/dashboard/audit.html`
- `templates/dashboard/campers.html`
- `tests/concurrency/test_email_registration.py`
- `tests/concurrency/test_invitations.py`
- `tests/conftest.py`
- `tests/integration/test_workflows.py`
- `tests/security/test_account_management.py`
- `tests/security/test_accounts.py`
- `tests/security/test_email_identity.py`
- `tests/security/test_google_oauth.py`
- `tests/security/test_staff.py`
- `tests/security/test_tenancy.py`

The local synthetic DB was stopped after validation; volumes retained. No SSH, registry
publication or live data change occurred. Commits are local; no Git remote push performed.

## Scanned email/profile test deployment — 2026-11-25/26

Current phase: continued phase 9 hardening and test deployment; phase 10 production acceptance
remains incomplete. Owner confirmed People API/scopes configured and requested scan/deploy,
with exact transcripts before connecting. Features remain separate commits `47bc241` (email)
and `1c2cbbf` (Google profile); this deployment has its own documentation/release commit.

Built and published `0.1.0-alpha.20261125-05df000f8652` for AMD64/ARM64 in the already approved
public Docker Hub repositories. Source snapshot SHA-256 is in the committed manifest. Build
and publication independently passed **271 PostgreSQL tests, 92.74% coverage**, Ruff/format,
Bandit, Gitleaks, Trivy source/configuration/dependency HIGH/CRITICAL and all eight image
vulnerability/secret gates. Both architectures passed non-root/missing-secret startup checks;
real proxy tests passed Google/People TLS and rejected unauthorized/private/metadata routes.
Poetry lock validation passed with existing metadata deprecation warnings; pip-audit found
no known vulnerabilities. Remote image-index digests were verified. DB/proxy filesystem
layers and all runtime image configurations match the previous release except labels.

Three additional synthetic PostgreSQL tests validated the exact deployment wrapper's
preflight/preservation, secondary-email refusal and rollback on an injected preservation
mismatch. Initial fixture-loader and deferred-constraint teardown errors were corrected
without changing application controls. Source/docs and exact deployment/recovery bundles
passed secret scanning. No tests, findings or security rules were suppressed.

The complete transcript, bundle contents and follow-ups were disclosed before their SSH
connections. Baseline lock/Compose checks passed. Web stopped for an encrypted, authenticated
snapshot, then `accounts.0003_email_identity` applied under the migrator in tenant scope.
Before commit, in-memory comparisons confirmed preserved data and expected email/security-
version changes. Old sessions retired; recent legacy lockouts carried forward. Reviewed
runtime grants/RLS reapplied; assets collected; digest-locked services started. No account
merges, approval/permission/password/MFA/Google-link changes, data restore or secret rotation.

The first runtime probe incorrectly expected strict GoogleSession to return unauthenticated
401/403. Its error handler stopped web; the corrected operator probe retained TLS and all
application controls. A subsequent SSH reset prevented a success claim. Read-only status
showed healthy new services; final verification was repeated with stdin isolated and an
explicit completion marker after another ambiguous zero exit. Final deployment, database,
container, network, schema, Google-cert/People TLS and public HTTPS/banner/CSRF/header/host/
SNI/body-limit/OAuth-scope/PKCE/nonce/form/asset checks **passed**. Human consent, actual profile
retrieval and approved-user Google sign-in were not performed or claimed.

Security architecture: unchanged modular monolith, per-campground identities/schema/RLS,
separate migrator/runtime roles and production controls under a development banner. Only the
previously approved People scope/host expansion (SD-029) is activated. New migration protects
identity continuity, sessions and lockouts. No new dependency or migration was authored in
this deployment task; existing accounts.0003 was applied. No new vulnerability identified,
prior vulnerability newly resolved, new security regression observed or pending approval.
The operator-probe defect was resolved; existing provider/shared-host/source-visibility risks,
external credential finding and lower-severity/manual/production gates remain unchanged.

Files modified/added in this deployment task:

- `README.md`
- `docs/aws-email-profile-deployment-transcript.md` (all commands/scripts and wrapper tests)
- `docs/backup-and-restore.md`
- `docs/container-publishing.md`
- `docs/deployment.md`
- `docs/email-identity.md`
- `docs/google-oauth.md`
- `docs/implementation-progress.md`
- `docs/security-decisions.md`
- `docs/security-findings.md`
- `releases/0.1.0-alpha.20261125-05df000f8652/README.md`
- `releases/0.1.0-alpha.20261125-05df000f8652/manifest.json`
- `releases/0.1.0-alpha.20261125-05df000f8652/images.env`

Private transfer/test harness files remain ignored under `.runtime/aws-email-upgrade-05df000f8652/`;
no secret/account data was copied into those artifacts. Application source is unchanged in
this deployment task. No Git remote push is authorized or performed.

### Executed commands and repeatable validation

```sh
poetry check --lock
.venv/bin/pip-audit --progress-spinner off
docker start campground-test-db-hardened
TEST_DATABASE_PORT=55433 .venv/bin/python scripts/release_images.py build --namespace thecyberbutler --version 0.1.0-alpha.20261125
SSL_CERT_FILE=/etc/ssl/cert.pem TEST_DATABASE_PORT=55433 .venv/bin/python scripts/release_images.py publish .runtime/releases/candidate-v63y9q1e/manifest.json --public-approved
TEST_DATABASE_PORT=55433 sh scripts/test.sh .runtime/aws-email-upgrade-05df000f8652/test_migrate_email.py -q --assert=plain --tb=no --show-capture=no
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
.venv/bin/python .runtime/aws-email-upgrade-05df000f8652/check_public_ui.py
```

Do not republish an existing immutable tag or rerun a completed one-time deployment. For a
fresh regression check use the synthetic DB and
`TEST_DATABASE_PORT=55433 sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85`.
Build creates a new private candidate path; the named candidate above records this run only.
Remote commands and exact follow-up validation are preserved in the transcript.

Remaining/unexecuted: interactive Google consent/name/phone/manual fallback/approved-login/MFA
acceptance; a new mutmut campaign; full isolated/off-host recovery; host storage/firewall/IAM
review; certificate renewal/alerts; broad browser/accessibility/load testing; SMTP delivery;
and unfinished specification features/release gates. Optional mutation command with synthetic
DB running: `.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900`.
Recommended next: complete human Google acceptance, then recovery/host/operational review.
Keep inventory inactive and booking closed until authoritative campground review. This is
not production-ready and must not accept real camper data before outstanding gates are met.

Final source/release/documentation Gitleaks and Trivy gates and `git diff --check` passed.
The synthetic local PostgreSQL container was stopped with its volume retained. No additional
AWS mutation followed successful final acceptance. Deployment records were committed as one
focused release milestone; no Git remote push was performed.

## Google login diagnosis and owner-authorized Camper approval — 2026-11-26

Current phase: phase 9 test acceptance/hardening; production gates unchanged. The owner
reported 403 after fresh Google authorization and supplied a HAR. Inspected only sanitized
metadata: callback 403, one value per callback parameter, initial app sign-in absent and
cookie headers absent from the export (not proof the browser omitted them). OAuth codes,
state, Google identifiers and raw content were never displayed, copied into the repository,
replayed or uploaded; the original sensitive capture remains in the owner's Downloads.

Exact remote diagnostic scripts were disclosed before SSH. Aggregate read-only checks found
one Google-linked account: active, unapproved, no privileged access. A synthetic invalid-code
token request through the approved TLS-verified Google proxy returned invalid_grant rather
than invalid_client; this supports client acceptance but does not establish a real user's
successful token exchange. Pending account approval is a definite application sign-in blocker.
The generic 403 hides the distinction between Google identity and campground authorization.

The owner explicitly confirmed the account is theirs and authorized Camper approval only.
Executed the disclosed existing protected `authorize_account` workflow under tenant scope,
with policy/account locks, exact eligibility/sole-account/role guards, audit and security-
version increment. Live in-memory comparisons confirmed other account fields and the Google
link unchanged. No permissions beyond ordinary Camper approval were granted; registration
approval, verification, MFA, rate limits, tenant isolation, closed booking and other controls
remain. No application code/image/config change, new dependency, migration, deployment or
secret rotation was necessary. The deployed release remains 0.1.0-alpha.20261125-05df000f8652.

Validation: **8 existing Google policy/login/MFA tests passed** (55 outside the targeted
selection deselected) and **3 synthetic approval-wrapper tests passed**, including ambiguous
selection refusal and transactional rollback on unexpected data change. The live audited
approval and preservation checks passed. No full-suite rerun, image build/scan, mutation
campaign, or real human Google sign-in was performed/claimed for this operator task.

No application authentication vulnerability was identified or newly resolved. This was an
intended authorization gate plus unclear error presentation. No controls were weakened and
no security approval is pending after the owner's scoped confirmation. HAR code/state are
sensitive artifacts, not evidence of a newly discovered public credential leak. Existing
external/host/lower-severity/manual production findings remain open.

Files modified: `docs/google-login-diagnosis.md`, `docs/google-oauth.md`,
`docs/security-decisions.md`, `docs/implementation-progress.md`. Private diagnostic/approval
and synthetic test scripts are ignored under `.runtime/google-login-diagnosis-20261126/`.
Exact commands/results and local repeat-validation commands are in the diagnosis document.
Do not rerun the one-time approval against an already approved account.

Next: owner starts a fresh Google login and confirms dashboard access; no automatic login
was performed on their behalf. If it still fails, diagnose the next boundary without assuming
approval was the only possible cause. Improve pending-approval messaging in a separately
reviewed implementation without account enumeration. All existing recovery/host/manual
acceptance and production gates remain; this is still not production-ready.

Final Gitleaks scans passed for source/documentation and the private diagnostic scripts;
`git diff --check` passed. The synthetic local DB was stopped with its volume retained.
This operational diagnosis/approval record is one focused Git commit; no remote Git push.
