# Implementation progress

Updated: 2026-11-24. Status: development; **not approved for production**.

Latest milestone: SaaS isolation implemented; 112 PostgreSQL tests passed (92.51% coverage).
See **SaaS implementation** below for current changes, findings, commands and remaining gates.
Earlier sections preserve the prior application/proxy validation history.

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

The owner-created `.vscode/` directory was left untouched. The isolated HTTPS validation
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
Removed: `Caddyfile`, `Caddyfile.dev`. Earlier application changes and owner `.vscode/` files remain intact.

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

Earlier application and Traefik changes remain intact. Owner `.vscode/` files were not edited.
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
