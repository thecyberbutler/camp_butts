# Incident response

1. **Identify:** record UTC time, affected versions, symptoms and audit event identifiers.
   Never copy credentials or camper data into tickets. Preserve protected evidence with
   restricted access and hashes; avoid contaminating the host or publishing exploit details.
2. **Contain:** isolate affected public access without deleting evidence. For accounts,
   deactivate affected users and revoke sessions; for container/host compromise, isolate
   the host and work from trusted administration hardware. Do not weaken controls to keep
   the service running. Notify the owner through an established private channel.
3. **Rotate:** treat exposed signing/DB/SMTP/MFA/session/recovery/invitation material as
   compromised. Revoke compromised keys rather than retaining them as fallbacks. A leaked
   MFA encryption key plus database contents requires reenrollment and recovery-code
   replacement; key rotation alone does not revoke copied TOTP secrets.
4. **Investigate:** review account/permission changes, reservation manipulation, export
   events, failed logins, images/dependencies, uploaded files (when supported), backup access
   and operator actions. Preserve audit data before cleanup. A DB or host administrator
   may have altered logs; local audit is not tamper-proof against those actors.
5. **Remediate:** fix root causes, add regression tests, patch trusted dependencies, rebuild
   from reviewed source and immutable image digests. For host compromise, replace the host;
   do not trust a cleaned container on an untrusted host. Quarantine malicious media without
   serving it. For database compromise, compare occupancy and privilege state to trusted
   records. Review all affected backups and recovery keys after backup compromise.
6. **Recover:** restore into isolation, invalidate stale sessions/tokens, verify grants,
   MFA, TLS, CSP, CSRF and occupancy integrity, then get owner authorization to reopen.
   Suspected administrative compromise requires reviewing all subordinate accounts and
   configurations. Vulnerable dependency findings remain open until patched and validated.
7. **Review:** document scope, impact, timeline, evidence, notifications, residual risks,
   corrective actions and follow-up owner. Handle applicable notification obligations with
   appropriate advice; do not invent reporting deadlines. Update threat model/decisions.

Production prerequisites: named incident owner, private reporting channel, tested contact
tree, offline recovery credentials and a rehearsed recovery procedure.

For proxy compromise, isolate the edge, rotate/revoke affected TLS and ACME account
credentials, and rebuild Traefik from the reviewed digest/configuration. Treat both the
current Traefik volume and retained legacy Caddy certificate volumes as sensitive evidence.
Do not enable the dashboard, Docker provider, debug/access logs or TLS bypass for diagnosis.


For a campground-specific incident, disable routing with the protected provisioning command
`docker compose run --rm provision --deactivate --campground SLUG`, preserve its schema,
audit and encrypted backups, and revoke affected account sessions within that campground.
Deactivation denies subsequent tenant resolution; in-flight transactions may finish. Quiesce
web/workers when immediate containment is required. Review other campgrounds if the exploit
could cross schema or application boundaries. Shared runtime/signing/MFA/DB/host compromise
requires platform-wide containment and review; do not assume schema isolation contains it.
Never restore another campground's schema under a new identity without an explicit reviewed
migration and token/key/session revocation procedure.

## Public-source credential exposure

If reference material contains a credential, do not reproduce its value in tickets, logs,
fixtures or responses. Record only its type/location and exclude the asset from imports.
Credential rotation/removal on an external source requires that source owner's action;
do not claim upstream remediation. The public campground PDF finding is recorded in
`security-findings.md`; no original PDF was added to the application.

## Publishing credential or image compromise

Revoke compromised Docker Hub tokens, stop publication, preserve trusted build hashes and
digest records, and review registry access/visibility. Never print tokens or export Docker
credential-store contents. Alert affected operators with verified replacement digests;
review any deployment that pulled a compromised artifact. Rebuild from reviewed source,
rerun gates and rotate application secrets if runtime compromise is suspected. Deleting or
privatizing a public image cannot recall copies already downloaded.

For the AWS public development host, use the strict known-host SSH alias `camp-butts-test`.
Disclose exact remote commands before execution as requested by the owner. Stop only project
`camp-butts-test` to contain exposure; preserve volumes, protected secrets and evidence. Do
not paste Docker inspect/environment/log output into incident reports. The visible test
banner does not reduce incident severity or authorize real personal data on an unaccepted host.
