# Security decision register

All entries dated 2026-11-24; review before production and by 2026-12-24.
No project-owner security exception has been requested, granted or inferred.
These decisions implement the supplied security requirements; they do not waive them.

| ID | Decision and justification | Alternatives / security impact | Residual risk | Approval status / rollback |
|---|---|---|---|---|
| SD-001 | Modular Django monolith; no managed services | Reject external managed SaaS and extra service boundaries | Host remains trust root | Required architecture; no exception; revert unpublished code |
| SD-002 | Unique per-environment file secrets, fail closed on missing/weak/overpermissive files | Reject plaintext env values and built-in defaults | Compose mounts are not encrypted; host encryption needed | Required protection; rotate and revoke on rollback |
| SD-003 | Allauth + Argon2id + Axes, separate Fernet MFA key | Reject custom authentication/cryptography; Fernet from cryptography | Encryption does not protect compromised runtime | Required protection; preserve enrollment and keys during rollback |
| SD-004 | Approval-first registration; SMTP-dependent verification/recovery stay unavailable without SMTP | No automatic verification fallback | Human approval identity checks required; email not trusted without verification | Conservative initial mode; no exception |
| SD-005 | Unified daterange exclusion for reservation and block | Reject check-then-insert only and separate block tables | Privileged DB owner can change constraints | Required integrity; never drop constraint to roll back app |
| SD-006 | Split DB credentials; append-only runtime audit; private networks; non-root containers | Reject superuser runtime and public DB/web ports | Host/root DB compromise | Required isolation; stop services before any rollback |
| SD-007 | No raw SVG or arbitrary uploads until safe processing is tested | Controlled numeric map coordinates and escaped labels | Feature incomplete until validated | Surface stays closed; no exception |
| SD-008 | Enforced camper 30-minute idle / 12-hour absolute; privileged 15-minute idle / 4-hour absolute; reauth 5 minutes | Reject indefinite sessions; no increases without owner approval | Stolen active sessions valid within bound; review before release | Conservative initial ceilings, not recorded owner approval |
| SD-009 | Encrypt signed database sessions with a distinct Fernet key; hash authentication-cache keys | Keeps temporary MFA enrollment material and OTP-derived cache identifiers out of plaintext storage | Compromised runtime can decrypt; key rotation invalidates sessions | Security improvement; no exception |
| SD-010 | Recheck staff identity, security stamp, MFA and permissions after acquiring the policy/account locks | Prevents stale requests after committed account/permission revocation; no client role input | Host operators must use serialized management paths | Security improvement; never replace with cached-only authorization |
| SD-011 | Camper deactivation/reactivation increments security version; privileged targets excluded even while inactive | Old sessions never revive on reactivation; no privilege-management web endpoint | Lost-MFA operator recovery remains unfinished | Security improvement; no exception |
| SD-012 | Patched Alpine Python/PostgreSQL images; DB starts non-root with all capabilities dropped | Removes vulnerable unused runtime installers/helpers; preserves SCRAM, constraints and role separation | Rebuild/scan each image; never reuse Debian physical DB volumes across libc variants | Security improvement; use logical migration into new volumes; preserve old volumes for recovery |
| SD-013 | Preserve Caddy's two unresolved dependency findings as release blockers | No suppression, speculative crypto fork, or weaker TLS/proxy alternative | Reported denial-of-service risks remain; applicability review is incomplete | No exception requested or granted; superseded for current deployment by SD-014; retain historical findings |

| SD-014 | Replace Caddy with digest-pinned Traefik 3.7.20 using file routing, exact hosts, TLS ≥1.2, strict SNI, 64 KiB body limit and bounded timeouts | Preserves three-container architecture; no Docker socket, provider credentials, API/dashboard or plugins; no trusted external forwarding peers | Public ACME issuance/renewal still needs deployment validation | Owner explicitly requested “lets replace Caddy with Traefik” on 2026-11-24; architectural approval only, not permission to weaken controls |
| SD-015 | WhiteNoise 6.12.0 serves collected read-only public assets through existing Django container | MIT, no required transitive dependencies, reviewed changelog and vulnerability audit; no development static server, extra container or arbitrary path mapping | Static traffic consumes bounded application workers; load validation remains | Security-preserving implementation detail of approved proxy substitution; no exception |
| SD-016 | Development-only localhost CA/leaf generation using established cryptography APIs; private CA key discarded, leaf key 0600 | Keeps certificate/hostname verification enabled; production uses automatic ACME renewal | Development leaf expires after 30 days; regeneration requires explicit trust in new public CA | No weaker TLS alternative approved; fail closed on absent/insecure files and unknown SNI |

Rollback: stop public routing and restore a separately reviewed proxy/configuration only
after its security gates pass. Do not automatically reactivate the old vulnerable Caddy
image. Preserve old Caddy certificate volumes without mounting or exposing them; no
certificate/private-key migration or public deployment occurred in this development task.

Production release requires all gates in PROJECT_SPEC.md. A missing test, unavailable
scanner or unavailable database is not a reason to relax a requirement.


## Owner-requested SaaS architecture — 2026-11-24

The owner requested SaaS multi-campground support and explicitly answered:
“Separate accounts per campground (stronger isolation)” and “Shared application and database”.
These are architectural choices, not security exceptions. No weaker alternative is approved.

| ID | Decision | Security rationale and residual risk | Approval / rollback |
|---|---|---|---|
| SD-017 | Retain mandatory stack; one schema per campground in shared PostgreSQL | Preserves independent auth/MFA/cache/FKs/exclusions; avoids tenant-column rewrites in third-party auth; shared runtime compromise still affects all tenants | Implements explicit owner choices; rollback only with routing stopped and verified encrypted recovery, never strip RLS or expose legacy routes |
| SD-018 | Resolve active slug before auth; transaction-local schema/UUID, FORCE RLS with restrictive guard | Denies missing/wrong contexts and qualified cross-schema queries; runtime lacks DDL/BYPASSRLS | Security improvement; arbitrary SQL/code execution remains outside this boundary |
| SD-019 | Tenant-bind sessions, email-confirmation salts and password-reset hash input; preserve __Host cookies | Prevents replay across matching local IDs and copied session ciphertext; keeps established framework cryptography | Existing sessions and outstanding links invalidated; no insecure compatibility fallback; one active campground session per cookie jar |
| SD-020 | Operator-only register/adopt/migrate/grant/activate lifecycle | No web self-provisioning or platform permissions for campground staff; operator events inaccessible to runtime | Activation follows completed schema protections; explicit adoption preserves legacy public data/constraints |
| SD-021 | Disable content-type cache; scope authentication caches and commands | Prevents database-alias cache reuse across schemas and implicit default jobs | Private Django cache interface requires upgrade regression review; performance testing remains |
| SD-022 | Tenant-selected backup with RLS enabled; no routine backup BYPASSRLS | Prevents blank/mixed dumps and avoids expanding backup privileges; store registry binding under encryption | Full encrypted restore rehearsal and platform event recovery remain release gates; no claimed verification |

All changes preserve required TLS, MFA, CSRF, CSP, hashing, cookie/session ceilings,
rate limits, audit append-only permissions, container and database network boundaries.
No security exception or pending security approval exists. The owner-selected shared
trust roots and same-origin limitations are recorded in docs/saas-architecture.md.
