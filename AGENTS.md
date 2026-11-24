# AGENTS.md

## 1. Project Overview

This repository contains a fully self-hosted campground reservation web application.

The complete application requirements are defined in PROJECT_SPEC.md.

Read PROJECT_SPEC.md before implementing functionality or making architectural decisions.

Read the existing architecture, security documentation, threat model, security decision records, and implementation progress before modifying the application.

---

## 2. Highest-Priority Requirement: Security

SECURITY IS THE HIGHEST PRIORITY OF THIS PROJECT.

Security takes precedence over functionality, performance, compatibility, convenience, development speed, and ease of implementation.

Under no circumstances may an agent independently make or implement a decision that knowingly or potentially reduces the security posture of the application.

Any proposed change that could potentially weaken security must receive explicit approval from the project owner before implementation.

This rule applies to:

- Production code.
- Development code.
- Test code.
- Configuration.
- Infrastructure.
- Dependencies.
- Authentication.
- Authorization.
- Database permissions.
- Container permissions.
- Deployment.
- CI workflows.
- Administrative interfaces.
- Documentation.
- Temporary workarounds.

Do not interpret general permission to develop the application as permission to accept additional security risk.

Do not assume that approval for one security exception applies to another.

Silence does not constitute approval.

If a security conflict occurs, preserve the more secure implementation.

Continue unrelated work where possible.

---

## 3. Security Approval Requirements

Before implementing any potentially security-reducing change, provide:

- Description of the proposed change.
- Reason for the change.
- Existing protections affected.
- Potential vulnerabilities introduced.
- Potential impact.
- Safer alternatives.
- Recommended mitigations.
- Temporary or permanent status.
- Rollback plan.
- Recommendation.

Wait for explicit approval before implementing the proposed security-reducing change.

Document granted approvals in docs/security-decisions.md.

Do not fabricate approval.

Do not implement a change merely because it can be reverted later.

---

## 4. Prohibited Security Workarounds

Never independently:

- Disable CSRF protection.
- Disable HTTPS.
- Disable certificate verification.
- Weaken authentication.
- Weaken authorization.
- Bypass MFA.
- Disable rate limiting.
- Weaken password hashing.
- Increase approved session lifetimes.
- Relax CSP.
- Expose internal services publicly.
- Expand container privileges.
- Expand database permissions unnecessarily.
- Use wildcard production hosts.
- Enable production DEBUG.
- Introduce default production credentials.
- Bypass input validation.
- Disable secure cookie settings.
- Suppress security findings without documented review.
- Remove security regression tests.
- Disable security checks to make CI pass.
- Remove database integrity constraints.
- Introduce unsafe temporary workarounds.

Do not weaken security controls to resolve application errors.

Correct the underlying implementation instead.

---

## 5. Secrets and Sensitive Information

Treat all secrets as confidential.

This includes:

- Passwords.
- Password hashes.
- API keys.
- Encryption keys.
- Signing keys.
- Database credentials.
- SMTP credentials.
- Authentication tokens.
- Session identifiers.
- MFA secrets.
- Recovery codes.
- Invitation secrets.
- TLS private keys.
- Backup credentials.

Never expose secrets through:

- Source code.
- Version control.
- Logs.
- Audit records.
- Test output.
- Error messages.
- Documentation.
- Terminal output.
- Docker images.
- Docker build arguments.
- Frontend code.
- HTTP responses.
- Task summaries.

Prefer protected file-based secret injection.

Use cryptographically secure secret generation.

Production startup must reject missing or insecure required secrets.

Do not read, print, or transmit existing secrets unnecessarily.

Do not send source code, credentials, or personal information to unapproved external services.

If a secret is discovered, report its location and type without reproducing its value.

---

## 6. Mandatory Technology Stack

Use:

- Python 3.13.
- Django 5.2 LTS.
- Poetry.
- PostgreSQL.
- Psycopg 3.
- Django Templates.
- HTMX.
- Bootstrap 5.
- Vanilla JavaScript.
- Docker Compose.
- Gunicorn.
- Caddy.
- Django authentication.
- django-allauth.
- Argon2id.
- Django Axes.

Use supported, security-patched versions.

Do not replace the required technology stack without explicit architectural approval.

Do not introduce managed SaaS services.

Do not introduce microservices.

Do not introduce unnecessary infrastructure.

Serve frontend dependencies locally.

---

## 7. Development Rules

- Favor secure, simple, maintainable implementations.
- Use a modular monolithic architecture.
- Apply the principle of least privilege.
- Apply defense in depth.
- Use secure defaults.
- Fail closed.
- Validate untrusted input.
- Enforce authorization server-side.
- Use object-level authorization.
- Keep complex business logic out of views.
- Centralize reservation policies.
- Use atomic transactions.
- Avoid duplicated security logic.
- Follow existing project conventions.
- Use Python type hints where practical.
- Avoid unrelated changes.
- Do not collect unnecessary personal information.

Do not implement custom cryptography when established framework or library functionality exists.

Do not trust frontend validation, hidden controls, cookies, headers, or user-supplied role information.

---

## 8. Authentication Requirements

- Use Django session-based authentication.
- Use Argon2id password hashing.
- Support self-service registration.
- Assign new accounts the least-privileged camper role.
- Require MFA for privileged accounts in production.
- Offer MFA to campers.
- Enforce authentication rate limiting.
- Protect account recovery.
- Prevent account enumeration.
- Rotate session identifiers appropriately.
- Invalidate sessions after relevant account security changes.
- Require recent reauthentication for sensitive operations.
- Prevent alternate endpoints from bypassing MFA.

Never store plaintext passwords.

Never create hidden authentication bypasses.

Never create universal administrative passwords.

---

## 9. Authorization Requirements

Every protected request must enforce appropriate authorization.

This includes:

- Standard Django views.
- HTMX endpoints.
- Form submissions.
- Administrative actions.
- Reservation operations.
- Report exports.
- File retrieval.
- Notification endpoints.
- Account management.
- Future API endpoints.

Do not rely on UUIDs, URL obscurity, hidden buttons, or client-side checks for authorization.

Prevent insecure direct object references.

Use deny-by-default access control.

---

## 10. Critical Reservation Requirements

- PostgreSQL must enforce campsite occupancy integrity.
- Overlapping active reservations must be prevented.
- Maintenance blocks must participate in occupancy constraints.
- Check-in dates are inclusive.
- Check-out dates are exclusive.
- Availability must be revalidated during reservation creation.
- Reservation operations must be transactional.
- Concurrent requests must not bypass booking policies.
- Duplicate submissions must be handled safely.
- Unauthorized reservation access must be prevented.
- Staff overrides must be authorized and audited.
- Staff overrides must never violate database integrity constraints.

Do not remove database constraints to resolve application errors.

---

## 11. Database Security

- PostgreSQL must not be publicly exposed.
- Use least-privileged database roles.
- Do not use a database superuser for normal application operations.
- Separate migration and runtime permissions where practical.
- Use parameterized queries.
- Prefer Django ORM.
- Do not concatenate user input into SQL.
- Protect sensitive data.
- Encrypt backups.
- Do not use production data in development environments unnecessarily.

---

## 12. Frontend Security

- Preserve Django template autoescaping.
- Preserve CSRF protection.
- Use restrictive CSP.
- Avoid unsafe inline scripts.
- Avoid unsafe-eval.
- Avoid unrestricted HTML rendering.
- Treat uploaded SVG as potentially executable.
- Validate and sanitize uploaded content.
- Do not expose secrets in HTML or JavaScript.
- Do not introduce third-party tracking scripts.
- Do not use external CDNs.
- Ensure HTMX endpoints enforce normal security requirements.

Design frontend functionality to work with security controls.

Do not weaken security controls to accommodate frontend functionality.

---

## 13. Infrastructure Security

- Expose only the approved reverse proxy.
- Do not publicly expose PostgreSQL or Gunicorn.
- Use private Docker networking.
- Run application containers as non-root.
- Restrict Linux capabilities.
- Avoid privileged containers.
- Avoid Docker socket mounts.
- Use restrictive filesystem permissions.
- Protect persistent data.
- Use supported base images.
- Keep production and development environments isolated.
- Enforce production HTTPS.
- Validate production configuration.
- Fail startup when critical security configuration is missing.

---

## 14. Dependency Management

Use Poetry for Python dependency management.

Maintain pyproject.toml and poetry.lock.

Before introducing a dependency:

- Confirm necessity.
- Evaluate maintenance.
- Evaluate known vulnerabilities.
- Evaluate transitive dependencies.
- Evaluate license compatibility.
- Evaluate security impact.

Do not introduce unsupported or known vulnerable dependencies without required explicit approval.

Pin frontend dependencies.

Maintain dependency inventory.

Use trusted package sources.

Do not bypass integrity verification.

Run appropriate dependency security checks.

---

## 15. Testing and Validation

Write meaningful tests for new features and bug fixes.

Prioritize:

- Authentication.
- MFA.
- Authorization.
- Object-level access.
- Secrets protection.
- Reservation integrity.
- Database constraints.
- Concurrency.
- File upload security.
- Input validation.
- Production security configuration.

Use PostgreSQL for database-specific tests.

Do not replace PostgreSQL with SQLite for reservation integrity testing.

Do not delete, weaken, or silently skip security tests.

Do not claim tests have passed unless they were actually executed successfully.

If the project owner instructs that particular validation commands must not be executed, respect that instruction and provide the commands for manual execution.

Report unexecuted tests and security checks as unverified.

Do not modify security requirements merely because a test is difficult to implement or execute.

---

## 16. Security Scanning

Maintain appropriate security scanning using:

- Bandit.
- pip-audit.
- Gitleaks.
- Trivy or equivalent tooling.
- Django deployment checks.
- Appropriate frontend dependency review.

Document security findings.

Do not silently suppress findings.

Do not mark unresolved findings as resolved.

Do not claim automated scanning guarantees application security.

Applicable unresolved high or critical security findings must block production release unless explicitly approved by the project owner.

---

## 17. Documentation

Keep these documents current:

- README.md.
- PROJECT_SPEC.md.
- SECURITY.md.
- docs/architecture.md.
- docs/deployment.md.
- docs/administration.md.
- docs/backup-and-restore.md.
- docs/security.md.
- docs/threat-model.md.
- docs/security-decisions.md.
- docs/incident-response.md.
- docs/dependency-inventory.md.
- docs/implementation-progress.md.

Document significant architectural decisions.

Document security implications.

Document residual risks.

Document explicit security approvals.

Do not autonomously edit mandatory security requirements to permit an otherwise prohibited implementation.

---

## 18. Implementation Progress

Update docs/implementation-progress.md throughout development.

Include:

- Current phase.
- Completed functionality.
- Remaining functionality.
- Known limitations.
- Pending security approvals.
- Security findings.
- Testing status.
- Recommended next steps.

Never represent incomplete or unverified functionality as completed or verified.

---

## 19. Completion Requirements

At the conclusion of every development task, provide:

- Summary of changes.
- Files modified.
- Database migrations introduced.
- Dependencies introduced.
- Architectural decisions.
- Security impact assessment.
- Security improvements.
- Potential security regressions.
- Pending security approvals.
- Identified vulnerabilities.
- Resolved vulnerabilities.
- Validation results.
- Unexecuted validation commands.
- Known limitations.
- Remaining work.
- Recommended next steps.

Explicitly report any decisions that could affect security.

If a potential security reduction is identified, do not implement it without explicit approval.

---

## 20. Final Directive

When faced with a choice between a more secure implementation and a less secure implementation, choose the more secure implementation.

When functionality cannot be implemented without weakening security, preserve security and report the conflict.

When an issue cannot be resolved without a potentially security-reducing decision, request explicit approval.

When uncertainty exists regarding the security impact of a change, treat the change conservatively and investigate before implementation.

Never compromise security for convenience.

Never compromise security to complete a task faster.

Never compromise security to make a test pass.

Never expose credentials to simplify debugging.

Never conceal security findings.

Never fabricate security approval.

Security must remain the highest priority of every development decision.
