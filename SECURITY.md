# Security policy

This application is under development. There is no supported production release yet.
Python 3.13, Django 5.2 LTS and PostgreSQL 17 are the selected supported series;
Traefik 3.7.20 and WhiteNoise 6.12.0 are the reviewed proxy/static-serving replacements;
always apply supported security patches and rerun the release gates.

Report suspected vulnerabilities privately to the project owner through an established
private contact channel. A dedicated reporting address must be published before release.
Do not post credentials, personal data, exploit payloads containing real data, or security
details in public issues. Provide affected version, impact and a synthetic reproduction.
Coordinate disclosure after containment and remediation; do not claim a response SLA
that the operator has not established.

Security takes precedence over functionality. No security exception is authorized by
ordinary development permission. Record any explicit owner exception, scope, risk,
mitigation, review date and rollback in docs/security-decisions.md. Applicable unresolved
high/critical findings block release. Automated scans are evidence, not a guarantee.

Update by reviewing trusted release advisories, refreshing Poetry locks or image digests,
reviewing transitive changes/licenses, and executing tests/scans and isolated deployment
and restore checks before promotion. Never disable safeguards to get an update working.


Multi-campground security reports should identify the affected campground slug and a
synthetic cross-tenant reproduction without real account IDs, tokens or camper records.
Schema/RLS isolation does not contain a compromised shared process, signing/encryption key,
database administrator or host. Review all campgrounds after compromise of those trust roots.
See docs/saas-architecture.md and the updated threat model; production release remains blocked.

Public campground imports and mutation tests preserve the existing security requirements.
Imported drafts remain inactive with server-side booking closed; source credentials are
excluded. Mutation tools run only against disposable source copies and synthetic PostgreSQL
data, and are absent from the runtime image. See SD-023/024, `docs/security-findings.md` and
`docs/mutation-testing.md`. No additional security exception has been approved or inferred.

Docker Hub public distribution of the three campground images was explicitly approved by
the owner on 2026-11-24, including packaged source/dependency visibility (SD-025). This
specific approval does not permit secrets/data publication, weaker runtime controls or
bypassed production release gates. Published artifacts remain evaluation prereleases.

The owner-requested AWS development instance is governed by SD-026. Its test banner is
presentation only: public test operation retains production security controls and is not
production approval. Use synthetic data until host and recovery acceptance is complete.

Optional Google sign-in is the scoped owner-approved exception SD-027. Its dedicated egress
proxy must stay private, non-root and destination restricted. Report OAuth replay, tenant
confusion, unintended account linking, MFA bypass, token persistence or SSRF as security
issues. Do not attach live callback URLs, OAuth tokens, cookies or the protected client file.
Live consent validation and the existing production security release gates remain required.
