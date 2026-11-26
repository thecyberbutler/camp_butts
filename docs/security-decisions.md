# Security decision register

All entries dated 2026-11-24; review before production and by 2026-12-24.
SD-001 through SD-024 introduced no project-owner security exception. SD-025 records the
explicit owner approval for public image/source visibility only. All other security
requirements and release gates remain mandatory.

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

## Campground onboarding and mutation testing — 2026-11-24

| ID | Decision | Security rationale and residual risk | Approval / rollback |
|---|---|---|---|
| SD-023 | Offline, bounded, strict-schema initial campground import under migration identity; matching inactive tenant and empty data store; atomic audit and digest-based no-op retry | No URL fetching/SSRF, credentials, HTML trust, account creation, privilege grants or overwrite path. Only HTTPS links without URL credentials. Drafts inactive and booking switch closed; source discrepancies remain operator review items | Owner explicitly authorized inactive map drafts. No security exception. To withdraw publication, deactivate tenant routing; preserve audit/data rather than deleting history |
| SD-024 | Exact development-only mutmut 3.8.1; disposable allowlisted copies and random synthetic PostgreSQL DBs, minimal environment, private artifacts, one worker and bounded process lifetime | No mutants applied to application source, no production data/DB, no inherited pre-fork DB state. Raw test output discarded; error/no-test/timeout outcomes fail review. Local tests retain access to existing local validation tools, so this is controlled test execution, not an OS sandbox for hostile code | Owner requested mutation testing. No runtime dependency or weaker control. Remove dev tool/config if withdrawn; retain useful regression tests and reviewed findings |

Bandit B404/B603 at the wrapper's subprocess import/invocation were individually reviewed:
the executable is the repository's local mutmut binary; arguments are a fixed command,
one worker and a restrictive reservation-service selector. There is no shell or arbitrary
command input. Environment/cwd are constructed, streams discarded, and process group bounded.
The two specific annotations retain all other Bandit checks; no exploitable injection finding
or broad rule is suppressed. Re-review if executable/argument/environment handling changes.

No weakened security alternative was implemented. No pending security approval exists.
Shared runtime/host trust roots from SD-017 remain unchanged. The booking switch is additional
business protection; it does not replace authorization or PostgreSQL occupancy constraints.

## Docker Hub distribution — 2026-11-24

### SD-025: explicit public-image visibility approval

The owner requested build/tag/publication to Docker Hub and selected namespace
`thecyberbutler`. Private repositories were recommended. Docker Hub allowed the first
private repository but rejected the next due to the account's private-repository quota.
A single private repository with component tags was offered as the security-preserving
alternative. The owner explicitly answered: **“Three public repositories — approve source
visibility”** on 2026-11-24. This is a specific visibility approval, not a waiver of release
security gates or permission to publish credentials, camper data, or production state.

- Change/reason: distribute the three application/database/proxy images publicly to simplify
  pulls without on-host builds and avoid the private-repository quota.
- Protection affected: confidentiality/access restrictions on packaged application source,
  dependency versions and build metadata. Runtime authorization and data access are unchanged.
- Risk/impact: anyone can download, retain and inspect those distributable contents;
  dependency/source details can support attacker reconnaissance. Public copies cannot be recalled.
- Safer alternatives: one private repository with distinct component tags, a plan supporting
  three private repositories, or continued local builds. One private repository was recommended.
- Mitigations: reviewed allowlisted snapshot, no secret build arguments, no data volumes,
  per-architecture secret/vulnerability scans, local PostgreSQL/security tests, least-privileged
  runtime, non-latest prerelease tags, minimal provenance, digest-locked deployment references,
  credential-helper authentication with token material kept out of output/files/arguments.
- Scope/duration: permanent visibility choice for `thecyberbutler/campground-web`,
  `thecyberbutler/campground-db`, and `thecyberbutler/campground-proxy`; review by 2026-12-24.
  No other repository visibility, public application deployment, or stable release is approved.
- Rollback: stop further pushes, restrict/remove affected registry artifacts through a controlled
  operator action and retain reviewed deployment digests. Already downloaded public copies
  cannot be recalled. Rotate credentials if a leak is ever discovered; image deletion is not remediation.
- Status: **explicitly approved by project owner**, implementing their selected public option.
  Earlier “no exception” statements describe the earlier milestones and do not override this record.

The local publisher uses fixed subprocess argument arrays with no shell and withheld raw
output (narrow Bandit B404/B603 review). Its B108 annotation refers to a container-private
bounded noexec/nosuid tmpfs, not a predictable shared-host temporary file. Scanner containers
have read-only mounts/root filesystems, no capabilities, no Docker socket and no app secrets.
Only the host operator invokes Docker. No additional Python/runtime dependency is introduced.

## Public development instance and environment banner — 2026-11-24

### SD-026: presentation label independent of security mode

The owner requested a red `THIS IS A TEST INSTANCE` banner and deployment to their
AWS host `3.89.25.233`, using `camp-butts-test.thecyberbutler.io` and SSH alias
`camp-butts-test`. This authorizes this public development instance; SD-025 alone did not.
`APP_ENVIRONMENT` accepts only production/development/test. Development/test show the
banner on complete application HTML documents, including authentication and generic errors.
It cannot be changed by request input. HTMX fragments retain the document's existing banner;
JSON/downloads/redirects and proxy-generated transport errors are not HTML application pages.
Development/testing settings force their corresponding label. Invalid configuration fails.

The public development deployment uses **production Django settings and Gunicorn**, with
only the presentation label set to development. DEBUG remains false; HTTPS, secure cookies,
CSRF, MFA, rate limits, CSP, tenant RLS, separate migration/runtime roles, and container/network
boundaries are retained. No development reload server or source mount is exposed. Generic
error rendering avoids tenant/session/database context and does not echo internal diagnostics.

SSH uses the existing known-host entry with strict checking, batch mode, no agent/port
forwarding and no connection multiplexing. The preflight was shown before connecting; it
identified Amazon Linux 2023/x86_64, available sudo, no existing deployment or Docker, and
about 4 GB RAM. The host key was matched to the locally trusted entry, not independently
verified against the AWS console. Every remote command/script is disclosed before execution.

The fresh-host script uses Amazon's signed package repositories for Docker and a pinned
Docker Compose v5.8.0 official binary verified against its GitHub release SHA-256. No Docker
group membership is added. Dedicated UID/GID 10001, root-controlled deployment configuration,
0700 secret storage and 0600 fresh secret files preserve published-image boundaries. Existing
paths/identities/resources/subnet conflicts cause refusal. No local secrets, accounts or
production data are transferred. Import keeps all map drafts inactive and booking closed.
Raw provisioning output is withheld; credentials never enter command arguments or transcripts.

No weaker security alternative or new exception is approved/implemented. Residual risks:
public prerelease attack surface, shared host/runtime trust, unverified AWS storage encryption
and security-group configuration, finite test capacity, and outstanding production release
gates. Only synthetic test data may be used pending host/recovery/security acceptance.
Rollback stops this Compose project without deleting volumes/secrets; preserve evidence and
use compatible reviewed image digests. Do not restore stale sessions or remove constraints.
Deployment status and actual validation results are recorded in implementation-progress.md.

## Google sign-in — 2026-11-24

### SD-027: explicit Google identity and restricted egress approval

The owner explicitly requested Google OAuth and deployment to the existing AWS test site.
They supplied an External-audience test client and confirmed its protected file installation.
The client secret was entered by the owner on-host; it was not sent through chat.
After review of the existing no-Internet web boundary, the owner explicitly answered:
**“Approve restricted Google egress proxy”**. This is a scoped network/trust exception,
not approval for unrestricted Internet access, weakened MFA, CSP or TLS.

- Proposed change/reason: optional Google OpenID Connect authorization-code sign-in, using
  existing allauth; one private, non-root Squid CONNECT sidecar supplies necessary egress.
- Protections affected: external-identity independence and the web container's complete
  outbound isolation. Google becomes an identity/availability dependency and sees sign-in
  activity, client/domain and browser information. The app receives subject and email only.
- Risks: Google account/provider compromise, credential/state leakage, cross-tenant callback
  confusion, account-link takeover, proxy/DNS/SSRF abuse, and additional dependency upkeep.
- Alternatives: retain local-only login (preserves current isolation), or give web direct
  Internet egress (weaker, rejected). Restricted CONNECT is the recommended approved design.
- Mitigations: web stays on internal networks; proxy has no public port, DB network or app
  secrets; exact oauth2.googleapis.com/www.googleapis.com:443 allowlist, blocked private/
  metadata destinations, no TLS interception, credential logs or cache, non-root/readonly/
  cap-drop/no-new-privileges and resource/time bounds. Application transport additionally
  restricts exact methods/URLs, denies redirects, verifies TLS and bounds responses.
- Authentication: explicit per-campground file credentials; client/tenant/session-bound
  single-use state, PKCE and nonce; fixed RS256 signature/issuer/audience/expiry checks;
  no browser-token/One Tap endpoint; no auto-link by email, no stored access/refresh tokens.
  New Google registrations retain required details, policy consent, invitation and approval
  rules and uniform completion without auto-login. Existing linking/disconnection requires
  recent password reauthentication and privileged application MFA; link changes revoke sessions.
- Email trust: Google verifies current Gmail/Workspace ownership; arbitrary third-party
  Google account mailboxes do not gain locally verified email status from that assertion.
- Duration/scope: enabled only for configured campgrounds while Google login is enabled;
  initial scope is the owner's test client and test deployment. Review by 2026-12-24 and
  before production. Local authentication remains available; no production release waiver.
- Rollback: disable Google configuration and remove its optional Compose overlay/egress
  service; preserve tenant data/links and local auth. Revoke Google credentials if compromised;
  use the operator recovery process for Google-only accounts, never create a bypass.
- Distribution: reuse the already approved public campground-proxy repository with a separate
  google-egress prerelease tag. No fourth repository, camper data or runtime secret publication.

Implemented and deployed as the 2026-11-25 Google prerelease. Automated callback/concurrency,
real proxy, actual runtime boundary and public authorization-start checks passed. A human
Google consent/token exchange and successful approved-user sign-in remain unverified.

Implementation detail: SocialApp tables remain inaccessible to runtime. SocialToken permits
only SELECT/DELETE, because Django's normal account-unlink collector checks and removes
dependent rows even when token storage is disabled. INSERT/UPDATE and sequence permissions
are denied, and forced tenant RLS remains active. This prevents token persistence while
preserving the framework's safe unlinking semantics; it does not grant access to client
credentials. Regression checks cover unlink assurance/session revocation and runtime grants.

## SD-028: local interface modernization — 2026-11-25

The owner requested rounded edges, shading, softer transitions and more color interaction.
Implement in existing local CSS/Django templates with native disclosure controls, system
fonts and fixed decorative SVG. Retain allauth form attributes/slots, template escaping,
CSRF, restrictive CSP, authorization and the red test banner. No new script, third-party
asset/service, dependency, permission, migration or network is needed.

Alternative: a new frontend framework/animation or hosted asset service would add unnecessary
dependencies/trust. The existing stack meets this presentation requirement. Reduced-motion,
keyboard focus, labels and mobile overflow checks protect usability. No security reduction
or additional approval is proposed. Residual risks are unreviewed browser/screen-reader
combinations and existing application/release findings; this is not security certification.
Review before production. Rollback is a normal reviewed revert of the presentation commit,
without database, credential or permission changes. No live deployment is part of this task.

### SD-028 deployment follow-up — 2026-11-25

After visual review the owner explicitly requested “lets scan and deploy”. The resulting
interface prerelease uses the already approved public registry/test host/Google boundaries.
Both-architecture scans and source tests precede publication; verified immutable digests
are the only deployment image inputs. Prior/new infrastructure filesystem layers and runtime
configuration are compared before cutover. No migration/grant change is applied; consistency
checks fail closed. A directly encrypted pre-upgrade snapshot and separately protected key
are retained; compatible rollback restores previous image references and collected assets,
never database contents, constraints or secrets. The exact transcript is disclosed before
remote execution. No new security reduction or exception is requested. Existing host-local
backup limitations and all production gates remain; status is recorded in implementation progress.

## SD-029: Google name and optional phone import — 2026-11-25

The owner requested profile names/phone and explicitly approved after scope/egress disclosure:
“I approve name and phone import. If there are settings I need to update on the oauth client
please let me know.” This authorizes `profile`, `user.phonenumbers.read` and restricted HTTPS
to `people.googleapis.com` for the signed-in user's own phone numbers only. It does not
approve contacts access, token persistence, automatic email linking, verified-phone status,
MFA/recovery changes, unrestricted egress or other profile data retention.

Affected controls: minimum OAuth scopes/data collection and the two-host egress allowlist.
Risks: additional personal data and provider consent, transient access-token use at another
Google endpoint, and abuse of the permitted destination by a compromised runtime. Mitigate
with a fixed self-profile endpoint/field mask, TLS/redirect/response bounds, the existing
private non-root proxy and metadata denial, transient tokens, bounded validated fields,
editable signup confirmation, and no overwrite of existing account details. Missing/denied
phone access uses optional manual entry and does not grant identity assurance. Names-only
or fully manual entry preserve narrower data access; owner selected both imports.

Duration: while optional Google integration is enabled; review before production and by
2026-12-25. Rollback removes added scopes/People route and revokes the provider grant if
needed; keep local email/password authentication and existing MFA. Google Cloud People API
and consent Data Access configuration are operator prerequisites. No new client secret,
callback URL or JavaScript origin is required. Production scope verification remains a gate.

## SD-030: email-only account identification — 2026-11-25

Owner explicitly requested eliminating usernames and identifying accounts by email. Retain
immutable internal UUIDs and case-insensitive database email uniqueness per campground;
remove the obsolete user-name field/constraint only as part of that requested model change.
No account merging, mailbox verification assumption, role change or automatic Google linking.
Migration must fail closed on invalid/colliding stored emails, preserve existing brute-force
protection and invalidate old sessions/pending authentication. Historical migrations and
third-party Axes protocol field names are retained for compatibility, not selectable usernames.
The schema change requires a stopped-web, encrypted-backup deployment and is not compatible
with blindly restarting the previous username-based image. No live deployment is part of
this implementation task. Existing security controls and release gates remain mandatory.

### SD-029 / SD-030 deployment follow-up — 2026-11-25

The owner confirmed People API and consent scopes configured and explicitly requested scan
and test deployment, with the complete exact transcript shown before connecting. This uses
the existing SD-025 public-image, SD-026 test-host and SD-029 scope/egress authorizations.
No new security exception is inferred. Source/tests and both-architecture image/egress gates
precede publication; remote digests are independently verified. Root-owned verified script
copies and a host deployment lock protect execution.

The schema-aware procedure validates the sole tenant and exact migration plan, stops web,
creates and authenticates an encrypted DB snapshot, and applies accounts.0003 under the
migration identity inside a tenant transaction. Before committing, it compares preserved
model records and expected account/email changes in memory, with bounded reads and generic
failures. It prints no account data or hashes. Existing runtime grants/RLS are reapplied and
checked. Session retirement and legacy lockout carryover remain mandatory.

Unlike the prior presentation upgrade, any failure after web stops leaves it stopped for a
reviewed forward fix. An old username image must never run on the new schema; no automatic
DB restore or historical-session revival is authorized. Snapshot/key remain separately
protected on the same host, so full isolated/off-host recovery is still an open release gate.
Exact execution/results: `aws-email-profile-deployment-transcript.md`. Existing production
requirements, manual Google acceptance and provider/host/shared-runtime risks remain.

## Owner-authorized test Camper approval — 2026-11-26

Diagnosis found the sole Google-linked test account active but pending campground approval.
The owner explicitly confirmed “Yes—this is my account; approve Camper access” after review
of the exact protected command. Applied only ordinary Camper approval through the existing
`authorize_account` workflow, with policy/account locks, expected-state checks, audit and
security-version increment. The command compared other account fields and retained the
Google link. No new account, role elevation, email attestation, policy change, automatic
linking, MFA bypass, secret change or new security exception was introduced. Future accounts
still require the existing approval process. Do not infer broader authorization from this
individual approval. See `google-login-diagnosis.md` for evidence and exact commands.

## SD-031: owner-selected open camper registration and enabled test inventory — 2026-11-26

The owner explicitly instructed: “Individual regular camper accounts do not need to be
approved. Anyone needs to be able to create an account and create a reservation right away.”
For the separate inventory gate they specified that all campsites on the test instance be
available and the test banner serve as the notice that the data is not real. These are specific
authorizations for open regular-camper registration and the existing development instance's
test inventory; no broader authentication or production exception is inferred.

- Change/reason: select existing open registration for new campers and enable all existing
  test sites/booking so signup-to-reservation functionality can be exercised without staff
  approval. Use consistent synthetic capacities/hookups/positions and normal site descriptions.
- Protections affected: manual pre-registration vetting and the test inventory closure that
  prevented use of unverified map drafts. Open registration increases spam, impersonation and
  inventory-hoarding risk; synthetic attributes must never be treated as verified live inventory.
- Alternatives: retain approval or invitation-only signup, verified-email signup once approved
  SMTP is configured, or keep inventory closed/use a single labeled test campsite. The owner
  explicitly selected open signup and all test sites with the existing environment banner.
- Mitigations retained: new accounts only Camper; no staff/admin self-assignment; account and
  IP limits; policy consent; normal email-verification settings; no automatic email linking;
  MFA/recent assurance for privilege; tenant RLS; locked, audited transactions; PostgreSQL
  exclusion/foreign-key constraints; capacity/date/per-account booking limits; HTTPS/CSP/CSRF;
  no automatic signup login that would expose duplicate-account existence. No old inactive or
  pending accounts are silently activated. Original source import stays unchanged.
- Scope/duration: open registration is the owner's selected normal camper policy. Test-site
  activation/sample attributes are only for the existing test deployment and are rejected by
  the operation in production. Review before production; its actual roster and release gates
  remain mandatory. This does not enable unconfigured SMTP, remove Google's external Testing
  audience restrictions, or authorize a platform-wide administrator interface.
- Rollback: an audited policy transaction can close booking or require approval for future
  registrations. Preserve existing users, audit, occupancy and constraints; do not automatically
  revoke prior approvals or cancel reservations. Review any account restrictions individually.
- Recommendation/status: implement the explicitly requested open mode with existing controls,
  retain distinct protected administrator onboarding, and validate full signup/login/booking
  paths. Approved directly by the owner; exact operation in open-registration-test-transcript.md.

## Owner-authorized test Administrator promotion — 2026-11-26

The owner explicitly requested: “Please promote my account to Administrator for Georgia
Mountain Fairgrounds on the test instance and walk me through setting up MFA.” This
authorizes the specific existing owner account's tenant role elevation, not a superuser,
platform privilege, MFA bypass or broader role-policy change. Earlier identity confirmation
identified the sole Google-linked account as theirs; ambiguity now causes refusal.

Applied the existing audited authorize_account command under tenant/policy/account locks,
with exact permission-set, active/approved Camper, verified email and nonproduction guards.
The transaction increments security_version; old sessions fail. MFA and recent assurance
remain mandatory. Elevated campground permissions increase the impact of account compromise;
verified email, TOTP enrollment/use, protected operator access, audit and tenant isolation
remain the mitigations. Keeping the Camper role would preserve lower privileges but would
not meet the owner's administration request. Rollback uses a separately authorized audited
Camper role assignment/session revocation, preserving account data and MFA. Review before
production. No password or MFA material was created or displayed by the agent.

Current onboarding limitation: Google-only accounts without existing MFA cannot satisfy
the installed framework's MFA-enrollment reauthentication through Google. Use the protected
interactive local-password establishment procedure; do not disable reauthentication or
fabricate MFA assurance. Actual owner enrollment remains pending.

## Approved Codex Cloud build-host access — 2026-11-26

The owner reported a PostgreSQL image build blocked by denied access to
dl-cdn.alpinelinux.org. Proposed adding only that host to the existing restricted development
environment allowlist to obtain signed Alpine security updates over verified HTTPS. This
expands development egress/supply-chain exposure. Retaining the denial is the secure
alternative with incomplete setup; unrestricted networking or removing the libxml2 update
is not recommended. Keep digest pins, package verification, proxy controls and isolated
synthetic data. No application runtime/Google egress change is proposed. Remove the addition
to roll back; rebuilds may need it again. The owner explicitly approved on 2026-11-26:
“I approve adding dl-cdn.alpinelinux.org to the Codex Cloud environment’s restricted allowlist.”
Approval is complete for this host only; saving and runtime verification remain pending.
No access change was implemented from this local chat. Review before production use and
by 2026-12-26; this is a development-build grant, not application runtime egress approval.
See codex-cloud-setup.md for concrete validation and scope.
