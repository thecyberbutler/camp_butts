# Campground Reservation System
## Project Specification and Implementation Requirements

---

## 1. Project Objective

Develop a complete, production-ready, fully self-hosted campground reservation web application that allows campers to create accounts, view campsite availability, and reserve campsites for specified date ranges.

The owner requested multi-campground SaaS operation on 2026-11-24, with a shared
application and PostgreSQL database and separate accounts per campground. Initially
support approximately 100 registered campers per campground. Aggregate capacity must be
measured before production commitments. All mandatory security requirements remain in force.

Campground selection initially uses a URL parameter (`?campground=slug`) that resolves
through a protected directory to canonical `/c/slug/` routes. Selection does not grant
access. Each campground must have independent accounts, MFA, sessions, roles, policies,
inventory, reservations, notifications and audit history. Unknown, disabled or conflicting
selections must fail closed. Cross-campground access must be prevented server-side and
covered by PostgreSQL, HTTP, authentication-token and concurrency regression tests.

Use a modular monolith with one PostgreSQL schema per campground, transaction-local
context and forced row-security defenses. Platform provisioning remains a protected
operator action. Managed external SaaS dependencies and subscription billing remain out
of scope. See docs/saas-architecture.md for the architecture review and residual risks.

The application must be:

- Secure by design.
- Secure by default.
- Fully self-hosted.
- Responsive and mobile-friendly.
- Reliable.
- Maintainable.
- Extensible.
- Easy to deploy and administer.
- Independent of managed SaaS services.

Security is the most important requirement of this project and must remain the highest priority throughout its entire development and operational lifecycle.

---

## 2. Mandatory Security Directive

### 2.1 Security Is the Highest Priority

Security takes precedence over all other project requirements, including:

- Functionality.
- Performance.
- Development speed.
- User convenience.
- Administrative convenience.
- Ease of deployment.
- Backwards compatibility.
- Dependency compatibility.
- Reduction in development effort.
- Reduction in infrastructure requirements.
- Automated test completion.

Under no circumstances may a decision be made or implemented autonomously that knowingly reduces the security posture of the application.

This requirement applies to all application code, infrastructure, configuration, dependencies, administrative interfaces, development environments, deployment procedures, automated workflows, and documentation.

When choosing between multiple implementation options, favor the most secure practical implementation.

When security and another requirement conflict, security takes precedence.

### 2.2 Mandatory Security Approval Process

Any proposed decision, change, workaround, configuration, dependency, or architectural modification that could potentially lower the security posture of the application must receive explicit approval from the project owner before implementation.

This includes temporary changes, development-only changes, and changes intended to be reverted later.

Examples requiring explicit approval include:

- Disabling or weakening authentication.
- Disabling or weakening authorization.
- Removing or weakening input validation.
- Disabling CSRF protection.
- Relaxing Content Security Policy.
- Disabling HTTPS enforcement.
- Disabling certificate verification.
- Weakening password requirements.
- Reducing password hashing strength.
- Increasing session lifetimes beyond approved limits.
- Disabling rate limiting.
- Exposing internal services publicly.
- Expanding database permissions.
- Expanding container privileges.
- Running services as root unnecessarily.
- Introducing publicly accessible administrative interfaces without approved protections.
- Storing sensitive information in less secure locations.
- Introducing dependencies with known unresolved security vulnerabilities.
- Bypassing security-related tests.
- Suppressing vulnerability findings.
- Removing security-related logging.
- Introducing insecure compatibility workarounds.
- Expanding the application's trust boundaries.
- Introducing new third-party access to application data.

Before requesting approval, provide:

1. A description of the proposed change.
2. The reason the change is being considered.
3. The existing security protections affected.
4. The potential vulnerabilities introduced.
5. The potential impact and affected data.
6. The safer alternatives considered.
7. Recommended mitigating controls.
8. Whether the change is temporary or permanent.
9. A rollback plan.
10. A clear recommendation.

Do not implement the proposed change until explicit approval is received.

Silence, lack of feedback, previous unrelated approval, or general authorization to develop the application does not constitute security approval.

Approval must be specific to the proposed change and its documented risks.

If approval has not been granted, retain the more secure implementation and continue working on unrelated tasks where possible.

### 2.3 Security Regression Policy

Every change must preserve or improve the existing security posture.

Before implementing changes:

- Identify affected security boundaries.
- Evaluate potential security regressions.
- Consider abuse cases.
- Consider privilege escalation opportunities.
- Consider unauthorized data access.
- Consider concurrency-related vulnerabilities.
- Consider accidental information disclosure.

After implementing changes, perform appropriate security validation.

If a security regression is discovered:

- Do not consider the affected functionality complete.
- Document the finding.
- Correct the issue using a secure approach.
- Add regression tests.
- Request explicit approval if remediation requires accepting additional security risk.

Never weaken a security control merely to make a test pass.

### 2.4 Fail Securely

Security-sensitive functionality must fail closed.

When a system cannot reliably determine whether an operation is authorized, safe, or valid, deny the operation.

Examples:

- If authorization cannot be determined, deny access.
- If a reservation's validity cannot be determined, reject the reservation.
- If account eligibility cannot be determined, prevent booking.
- If required secrets are missing, prevent production startup.
- If production security configuration is invalid, prevent production startup.
- If certificate verification fails, do not establish an insecure connection.
- If security-critical validation fails, reject the request.
- If a security-critical rate-limiting mechanism fails, do not silently permit unrestricted access.

Never silently fall back to insecure behavior.

### 2.5 Security Standards

Use the following as development and review references:

- OWASP Application Security Verification Standard, targeting Level 2.
- OWASP Top 10.
- OWASP Cheat Sheet Series.
- OWASP Secure Coding Practices.
- Django security documentation.
- PostgreSQL security documentation.
- Docker security best practices.
- NIST digital identity and authentication guidance.
- Principle of least privilege.
- Defense in depth.
- Secure software development lifecycle practices.

Use current authoritative documentation when implementing security-sensitive functionality.

Do not claim formal compliance or certification unless independently verified.

---

## 3. General Development Instructions

- Review existing repository contents and development instructions before beginning implementation.
- Read AGENTS.md and this specification in their entirety.
- Use established software development best practices.
- Favor simplicity, security, maintainability, and reliability.
- Implement a modular monolithic architecture.
- Do not introduce microservices.
- Do not introduce Kubernetes.
- Do not introduce unnecessary infrastructure.
- Do not use managed database services.
- Do not use external authentication providers.
- Do not use external CDN-hosted frontend dependencies.
- Avoid unnecessary third-party dependencies.
- Use type hints throughout Python code where practical.
- Document major architectural decisions.
- Do not hardcode secrets, credentials, campground-specific information, or configurable reservation policies.
- Implement functional features rather than placeholder functionality.
- Follow the principle of least privilege throughout the application.
- Include comprehensive documentation.
- Include meaningful automated tests.
- Use explicit configuration rather than insecure implicit behavior.

Where requirements are not explicitly defined, make reasonable implementation decisions consistent with the project objectives, provided those decisions do not potentially weaken security.

Security-related ambiguities must be resolved conservatively.

---

## 4. Required Technology Stack

### 4.1 Backend

- Python 3.13.
- Django 5.2 LTS.
- Poetry for dependency management.
- Gunicorn as the production application server.
- Psycopg 3 PostgreSQL adapter.

Use supported, security-patched releases within the selected version series.

### 4.2 Frontend

- Django templates.
- HTMX.
- Bootstrap 5.
- Vanilla JavaScript.
- CSS.
- SVG for interactive campground maps.
- FullCalendar free features where appropriate.

All frontend dependencies must be served locally.

Do not use:

- React.
- Vue.
- Angular.
- External JavaScript CDNs.
- External font CDNs.
- Third-party tracking scripts.
- Third-party analytics services.
- Paid calendar components.

Do not introduce a separate frontend build architecture unless explicitly approved.

### 4.3 Database

- PostgreSQL 17 or a newer supported stable release.
- Django ORM.
- Django database migrations.
- PostgreSQL GiST exclusion constraints.
- PostgreSQL btree_gist extension.

### 4.4 Authentication

- Django built-in authentication.
- django-allauth.
- Django session-based authentication.
- Argon2id password hashing.
- Django Axes for login rate limiting.
- TOTP-based multi-factor authentication.
- Secure recovery codes.

Administrator and staff accounts must use multi-factor authentication in production.

Multi-factor authentication should also be available to campers.

### 4.5 Infrastructure

- Docker.
- Docker Compose.
- Traefik reverse proxy (owner-approved substitution, 2026-11-24).
- Gunicorn.
- Linux-compatible deployment.
- Persistent Docker volumes.
- Host cron or systemd timers for scheduled tasks.

### 4.6 Development and Testing

- pytest.
- pytest-django.
- pytest-cov.
- Ruff.
- mypy and django-stubs where practical.
- Bandit for Python security analysis.
- pip-audit for Python dependency vulnerability analysis.
- Gitleaks for secret detection.
- Trivy for container and infrastructure vulnerability scanning.
- GitHub Actions or an equivalent self-hosted CI system.

The production application must not depend on GitHub or any external CI service to operate.

Any proposed technology substitution must be documented. Changes potentially affecting security require explicit approval.

---

## 5. System Architecture

Implement a modular Django monolith.

The initial production deployment should consist of three primary containers.

### 5.1 Reverse Proxy Container

Responsible for:

- Traefik.
- HTTPS termination.
- HTTP-to-HTTPS redirects.
- Reverse proxying application requests.
- Security-related HTTP headers.
- Routing approved static files to WhiteNoise in the web container.
- Request size restrictions.
- Appropriate connection and request timeouts.

The reverse proxy must be the only publicly accessible application container.

### 5.2 Web Application Container

Responsible for:

- Django.
- Gunicorn.
- Authentication.
- Authorization.
- Reservation management.
- Administrative functionality.
- Application business logic.
- Frontend rendering.
- Serving only collected, read-only static assets using WhiteNoise.
- Notifications.
- Audit logging.

The web container must not publish its application port directly to the public network.

### 5.3 Database Container

Responsible for:

- PostgreSQL.
- Persistent application data.
- Database integrity constraints.
- Transactional consistency.

PostgreSQL must not expose a publicly accessible port.

### 5.4 Network Isolation

Create separate Docker networks where appropriate:

- Reverse proxy to application network.
- Application to database network.

The reverse proxy should not have direct database access.

The database should not require unrestricted internet access.

Restrict container-to-container communication to necessary services.

Do not mount the Docker socket into application containers.

Avoid host networking and privileged containers.

### 5.5 Capacity

The initial deployment should comfortably support approximately 100 registered campers using:

- 4 CPU cores.
- 8 GB RAM.
- 100 GB SSD storage.

These are initial sizing targets, not guaranteed performance requirements.

Do not weaken security controls to meet performance targets.

---

## 6. Repository Structure

Use a structure similar to the following:

```text
campground/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── security.yml
├── apps/
│   ├── accounts/
│   ├── campsites/
│   ├── reservations/
│   ├── dashboard/
│   ├── notifications/
│   ├── configuration/
│   └── audit/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── templates/
│   ├── base.html
│   ├── components/
│   ├── accounts/
│   ├── campsites/
│   ├── reservations/
│   └── dashboard/
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── maps/
│   └── vendor/
├── media/
├── scripts/
│   ├── entrypoint.sh
│   ├── generate-secrets.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── security-check.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── concurrency/
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   ├── administration.md
│   ├── backup-and-restore.md
│   ├── security.md
│   ├── threat-model.md
│   ├── security-decisions.md
│   ├── incident-response.md
│   ├── dependency-inventory.md
│   └── implementation-progress.md
├── .env.example
├── .gitignore
├── .dockerignore
├── .pre-commit-config.yaml
├── AGENTS.md
├── PROJECT_SPEC.md
├── SECURITY.md
├── infra/traefik/
├── Dockerfile
├── compose.yaml
├── compose.dev.yaml
├── manage.py
├── pyproject.toml
├── poetry.lock
└── README.md
```

Adjust the repository structure where appropriate without compromising security or maintainability.

---

## 7. Threat Modeling and Security Architecture

Before implementing major application functionality, create an initial threat model.

Maintain the threat model in `docs/threat-model.md`.

Identify:

- Application assets.
- Sensitive information.
- Authentication boundaries.
- Authorization boundaries.
- Network boundaries.
- Database access paths.
- Administrative interfaces.
- File upload interfaces.
- External dependencies.
- Backup and restoration processes.
- Development and deployment workflows.
- Potential attacker capabilities.
- Potential abuse cases.

Consider threats including:

- Account takeover.
- Credential stuffing.
- Brute-force authentication attacks.
- Password reset abuse.
- Account enumeration.
- Privilege escalation.
- Broken access control.
- Insecure direct object references.
- Cross-site scripting.
- Cross-site request forgery.
- SQL injection.
- Server-side request forgery.
- Malicious file uploads.
- Session hijacking.
- Session fixation.
- Unauthorized administrative access.
- Reservation manipulation.
- Reservation inventory exhaustion.
- Concurrent reservation abuse.
- Data exfiltration.
- Secret disclosure.
- Backup theft.
- Supply-chain compromise.
- Container compromise.
- Denial of service.
- Malicious or compromised administrators.

Document appropriate mitigations and residual risks.

Update the threat model whenever application architecture, security boundaries, or sensitive functionality changes.

---

## 8. Secrets Management

Protect all passwords, API keys, encryption keys, authentication tokens, recovery codes, database credentials, SMTP credentials, signing keys, and other sensitive information.

Treat secrets management as a critical security requirement.

### 8.1 Secret Storage

Secrets must never be:

- Hardcoded in source code.
- Committed to version control.
- Included in container images.
- Included in Docker build arguments.
- Written into Docker image layers.
- Included in frontend JavaScript.
- Included in public configuration files.
- Exposed through API responses.
- Included in error responses.
- Included in application logs.
- Included in audit records.
- Included in automated test output.
- Included in documentation.
- Printed to terminal output unnecessarily.
- Included in screenshots.
- Transmitted to external services without authorization.

Prefer file-based secret injection using Docker Compose secrets or appropriately protected mounted secret files.

Support environment variables containing paths to secret files.

Do not treat ordinary environment variables or Docker Compose secrets as automatically encrypted storage.

Protect secret files on the host with appropriate permissions and restrict access to the minimum required users and services.

Document the limitations of local secret storage.

### 8.2 Secret Generation

Provide a secure secret-generation script.

Generate secrets using cryptographically secure random number generators.

Do not use Python's random module for security-sensitive values.

Use Python's secrets module or an appropriate operating-system cryptographic random source.

Generate unique secrets for each deployment.

Never reuse:

- Django secret keys.
- Database passwords.
- Encryption keys.
- Service credentials.
- Development credentials in production.

Production startup must reject missing, placeholder, known-default, or otherwise invalid required secrets.

### 8.3 Secret Access

Grant access only to services requiring a particular secret.

For example:

- The reverse proxy does not need database credentials.
- The database does not need the Django secret key.
- The web application does not need host administration credentials.
- CI jobs should not have production database credentials.

Do not unnecessarily share secrets between services.

### 8.4 Secret Rotation

Document procedures for rotating:

- Django signing keys.
- Database credentials.
- SMTP credentials.
- Encryption keys.
- API keys.
- Administrative credentials.
- Recovery codes.

Ensure rotation procedures account for session invalidation, encrypted data, and compatibility requirements.

Do not retain compromised secrets for backwards compatibility.

### 8.5 Secret Detection

Implement secret scanning using Gitleaks or an equivalent tool.

Perform scanning:

- Before commits where practical.
- During CI.
- During release validation.

If a secret is discovered in version control:

- Treat the secret as potentially compromised.
- Document the incident without reproducing the secret.
- Notify the project owner.
- Recommend immediate revocation or rotation.
- Remove the secret from active code and configuration.
- Evaluate repository history remediation.

Deleting a secret from the latest commit is not sufficient remediation.

Never display an actual discovered secret in a task summary.

---

## 9. Authentication and Account Management

Implement a custom Django user model before creating initial database migrations.

Use Django AbstractUser as the foundation.

### 9.1 User Fields

Include:

- Unique user identifier.
- Username.
- Email address.
- First name.
- Last name.
- Phone number.
- Password hash.
- Account status.
- Registration timestamp.
- Last login.
- Staff status.
- Superuser status.

Use django-allauth's supported email verification mechanisms without creating conflicting sources of verification state.

Enforce appropriate case-insensitive uniqueness for usernames and email addresses at the database level.

Never store plaintext passwords.

### 9.2 Self-Service Registration

Users must be able to create accounts independently.

Registration fields should include:

- First name.
- Last name.
- Username.
- Email address.
- Phone number.
- Password.
- Password confirmation.
- Agreement to campground rules.
- Agreement to reservation policies.

Use server-side validation for every field.

Do not trust client-side validation.

Prevent users from assigning themselves roles, permissions, account approval status, or administrative privileges through manipulated registration requests.

New accounts must always receive the least-privileged camper role.

Record the applicable policy version and acceptance timestamp.

### 9.3 Registration Modes

Support administrator-configurable modes:

1. Open registration.
2. Administrator approval required.
3. Invitation-only registration.
4. Registration disabled.

Users must be able to register themselves whenever an applicable registration mode permits registration.

Administrator approval mode is the recommended secure initial production configuration.

Allow open registration when intentionally selected by the authorized administrator or project owner.

Email verification must be independently configurable subject to the production security policy.

When transitioning between registration modes, do not automatically grant privileges to previously restricted accounts.

### 9.4 Invitation Codes

Administrators should be able to:

- Generate invitation codes.
- Configure expiration dates.
- Configure maximum usage counts.
- Disable invitation codes.
- Review usage history.

Invitation codes must:

- Use cryptographically secure randomness.
- Have sufficient entropy.
- Be stored in a protected, non-recoverable form where practical.
- Be validated securely.
- Be protected by rate limiting.
- Expire appropriately.
- Be redeemed transactionally.
- Enforce usage limits under concurrent requests.
- Never appear in logs or audit records.

### 9.5 Password Security

Use Argon2id as the preferred password hashing algorithm.

Select appropriate hashing parameters based on current authoritative guidance and deployment hardware.

Do not independently reduce password hashing strength to improve performance.

Implement:

- A minimum password length of 15 characters as the default.
- Support for passwords of at least 64 characters.
- Support for password managers.
- Support for pasting passwords.
- Common-password rejection.
- Secure password comparison.
- Appropriate password hashing upgrade behavior.
- Reasonable maximum input sizes to prevent resource exhaustion.

Do not require arbitrary character composition rules or routine password changes unless justified by a specific security requirement.

Require password changes when compromise is suspected or confirmed.

Do not transmit passwords to external password validation services.

### 9.6 Multi-Factor Authentication

Require TOTP-based multi-factor authentication for administrator and staff accounts in production.

Offer TOTP-based multi-factor authentication to campers.

Protect TOTP secrets using appropriately reviewed application-level encryption and separately managed keys.

Recovery codes must be:

- Cryptographically generated.
- Single-use.
- Stored in hashed or equivalently protected form.
- Invalidated when replaced.
- Protected from logging.
- Displayed only when necessary.

Require recent reauthentication for sensitive MFA configuration changes.

Enforce MFA across every privileged authentication and administrative access path, including Django Admin.

Do not permit an alternate login endpoint to bypass MFA requirements.

Do not introduce hidden MFA bypasses, universal recovery passwords, or backdoor accounts.

Document a secure administrative recovery procedure.

### 9.7 Login Protection

Implement:

- Django Axes.
- Account-based and IP-based rate limiting.
- Appropriate progressive delays or temporary lockouts.
- Generic authentication failure responses.
- Credential stuffing protections.
- Brute-force protections.
- Authentication event logging.

Ensure client IP determination cannot be manipulated through untrusted forwarded headers.

Avoid permanent account lockouts that could be abused to deny legitimate users access.

### 9.8 Session Security

Use Django's server-side session framework.

Implement:

- Secure cookies in production.
- HttpOnly session cookies.
- Appropriate SameSite cookie configuration.
- Host-only cookies where practical.
- Session identifier rotation after authentication.
- Session invalidation after logout.
- Appropriate idle and absolute session expiration.
- Shorter session lifetimes for privileged accounts.
- Session invalidation following relevant password or privilege changes.
- Recent reauthentication for sensitive account operations.

Document proposed session lifetimes before production release.

Do not independently increase approved session lifetimes.

Do not place authentication tokens in browser localStorage.

Do not introduce JWT authentication without explicit architectural review.

### 9.9 Password Recovery

Implement secure password recovery when SMTP is configured.

Recovery tokens must be:

- Cryptographically secure.
- Time-limited.
- Single-use.
- Protected against replay.
- Invalidated appropriately.

Password recovery responses must not disclose whether an account exists.

Never email plaintext passwords.

Never display existing passwords to administrators.

Require secure recovery procedures for privileged accounts that do not silently bypass MFA.

When SMTP is unavailable, provide a documented administrator-assisted recovery process involving identity verification and secure credential establishment.

Do not use security questions or easily guessed personal information as an authentication factor.

### 9.10 Account Management

Users must be able to:

- Register.
- Log in.
- Log out.
- Change their password.
- Recover their account when supported.
- Update personal information.
- Configure MFA.
- Review active sessions where supported.
- Revoke other sessions.
- View reservation history.
- View current reservations.

Require recent authentication for sensitive operations such as changing passwords, changing email addresses, disabling MFA, or regenerating recovery codes.

When email verification is enabled, verify new email addresses before treating them as trusted recovery destinations.

Administrators must be able to:

- Create accounts.
- Edit accounts.
- Approve accounts.
- Deactivate accounts.
- Reactivate accounts.
- Assign authorized roles.
- Initiate secure account recovery.

Account deactivation must invalidate existing authenticated access.

---

## 10. Authorization and Permissions

Implement role-based access control using Django groups and permissions.

All protected operations must enforce authorization server-side.

Use a deny-by-default approach.

### 10.1 Camper

Can:

- View permitted campground information.
- View campsite availability.
- Create reservations.
- View their own reservations.
- Modify their own reservations when permitted.
- Cancel their own reservations when permitted.
- Manage their own account.

Cannot:

- View other campers' personal information.
- View other campers' private reservation details.
- Modify other campers' reservations.
- Access administrative functionality.
- Change application configuration.
- Grant themselves additional privileges.

### 10.2 Staff

Can perform authorized campground operational functions:

- View reservations.
- Create reservations on behalf of campers.
- Modify reservations.
- Cancel reservations.
- Block campsites.
- Check campers in.
- Check campers out.
- View campground occupancy.
- Search necessary camper information.

Staff should receive granular permissions.

Do not grant unnecessary administrative access.

### 10.3 Administrator

Can perform explicitly authorized administrative functions:

- Manage camper accounts.
- Approve registrations.
- Manage campsites.
- Configure campground policies.
- Manage invitation codes.
- Manage campground branding.
- Manage maps.
- Review audit logs.
- Assign permitted roles.

Restrict superuser accounts to necessary system administration.

Routine campground operations should not require unrestricted superuser privileges.

### 10.4 Object-Level Authorization

Every object-specific request must verify that the acting user is authorized to access the requested object.

Apply this requirement to:

- Standard views.
- HTMX endpoints.
- Form submissions.
- Administrative actions.
- File downloads.
- Report exports.
- Notification endpoints.
- Reservation details.
- Profile management.
- Any present or future API endpoints.

Do not rely on:

- Hidden frontend elements.
- Disabled form controls.
- Unpredictable identifiers.
- UUIDs alone.
- URL obscurity.
- Client-side JavaScript.
- User-supplied role information.

Prevent insecure direct object reference vulnerabilities.

---

## 11. Campsite Management

Create a campsite model supporting:

- Unique campsite identifier.
- Unique campsite number or name.
- Description.
- Campsite type.
- Active/inactive status.
- Maximum occupancy.
- Maximum RV length.
- Pull-through or back-in designation.
- Electrical availability.
- Electrical amperage.
- Water availability.
- Sewer availability.
- Wi-Fi availability.
- Pet-friendly status.
- Accessibility information.
- Campsite photographs.
- Map identifier.
- Display order.
- Creation timestamp.
- Modification timestamp.

### 11.1 Campsite Types

Support administrator-configurable campsite types.

Initial examples:

- RV sites.
- Tent sites.
- Primitive sites.
- Full-hookup RV sites.
- Partial-hookup RV sites.
- Cabins.
- Other.

### 11.2 Amenities

Support configurable campsite amenities.

Examples:

- 30-amp electrical service.
- 50-amp electrical service.
- Water.
- Sewer.
- Picnic table.
- Fire ring.
- Shade.
- Waterfront.
- Wi-Fi.
- Pull-through access.

### 11.3 Campsite Images

Support multiple photographs per campsite.

Store images locally using persistent storage.

Apply secure file upload requirements described in this specification.

---

## 12. Reservation System

The reservation engine is the application's primary business function.

Reservation integrity is a security and reliability requirement.

### 12.1 Reservation Fields

Include:

- Unique reservation identifier.
- Human-readable confirmation number.
- Camper.
- Campsite.
- Check-in date.
- Check-out date.
- Occupancy date range.
- Reservation status.
- Number of adults.
- Number of children.
- Number of pets.
- RV length when applicable.
- Camper notes.
- Private staff notes.
- Creation timestamp.
- Modification timestamp.
- Cancellation timestamp.
- Cancellation reason.
- Created-by user.
- Modified-by user.

Confirmation numbers must not function as authentication credentials.

Possession of a confirmation number must not grant access to private reservation details.

### 12.2 Reservation Statuses

Support:

- Pending approval.
- Confirmed.
- Checked in.
- Checked out.
- Cancelled.
- Rejected.
- No-show.

Define valid status transitions using centralized business logic.

Prevent unauthorized or invalid status transitions.

### 12.3 Date Handling

Use half-open reservation date ranges:

```text
[check_in_date, check_out_date)
```

The check-in date is inclusive.

The check-out date is exclusive.

A reservation from December 4 through December 7 occupies December 4, 5, and 6.

Another camper may reserve the campsite beginning December 7.

Use date-based occupancy rather than timestamps for campsite availability.

Use timezone-aware timestamps for application events.

The campground timezone must be configurable, defaulting to America/New_York.

### 12.4 Database-Level Reservation Integrity

Prevent overlapping campsite occupancy at the database level.

Use:

- PostgreSQL date ranges.
- Django DateRangeField.
- Django ExclusionConstraint.
- PostgreSQL GiST indexes.
- PostgreSQL btree_gist extension.

Use a unified occupancy model or equivalent database-enforced architecture to prevent conflicts between:

- Confirmed reservations.
- Pending reservations that hold inventory.
- Checked-in reservations.
- Maintenance blocks.
- Administrative blocks.

Do not rely exclusively on application-level availability checks.

Do not permit administrative overrides to violate occupancy constraints.

Ensure date ranges cannot be empty, invalid, or unbounded.

Use database constraints for critical data integrity rules wherever appropriate.

### 12.5 Transactional Safety

Reservation-related operations must use atomic database transactions.

Protect against:

- Concurrent reservation requests.
- Concurrent reservation modifications.
- Concurrent cancellations.
- Concurrent maintenance blocks.
- Concurrent reservation policy violations.
- Duplicate form submissions.
- Request retries.
- Race conditions.
- Time-of-check/time-of-use vulnerabilities.

Use appropriate row-level locking or equivalent mechanisms for camper-specific reservation limits.

Define consistent lock ordering where multiple records must be locked.

Handle integrity errors without exposing database internals.

A failed reservation operation must not leave partial occupancy or reservation records.

### 12.6 Availability Search

Allow users to search by:

- Check-in date.
- Check-out date.
- Campsite type.
- Required amenities.
- RV length.
- Electrical requirements.
- Occupancy requirements.
- Pet-friendly requirements.

Only return campsites available for the entire requested date range.

Limit excessively large date ranges and expensive search requests.

Revalidate all policies and availability when a reservation is submitted.

Never trust frontend availability results.

### 12.7 Reservation Confirmation

After successful reservation creation:

- Generate a unique confirmation number.
- Display a confirmation page.
- Add the reservation to the camper dashboard.
- Create an in-app notification.
- Send an email if enabled.
- Create an audit record.

Send notifications only after the database transaction commits successfully.

Use idempotent submission handling to prevent duplicate reservations and duplicate notifications.

---

## 13. Configurable Reservation Policies

Create database-backed configuration settings.

Support:

- Maximum consecutive reservation nights.
- Minimum reservation nights.
- Maximum active reservations per camper.
- Maximum advance booking period.
- Minimum advance booking notice.
- Same-day reservation availability.
- Cancellation deadline.
- Modification deadline.
- Check-in time.
- Check-out time.
- Reservation approval requirements.
- Pending reservation inventory holding.
- Pending reservation expiration period.
- Whether campers can reserve multiple campsites.
- Whether campers can cancel reservations.
- Whether campers can modify reservations.
- Authorized staff policy overrides.

Provide conservative defaults and document them.

Validate configuration combinations.

Prevent conflicting or invalid settings.

Ensure policy enforcement cannot be bypassed through concurrent requests.

Staff overrides must:

- Require explicit permission.
- Require a documented reason.
- Create an audit record.
- Never bypass authorization or database integrity constraints.

Distinguish ordinary campground business policies from security policies.

Security-sensitive settings must not be freely weakened through routine administrative configuration.

Any supported security-affecting configuration must have documented security boundaries and project-owner approval requirements.

---

## 14. Maintenance and Campsite Blocking

Authorized staff and administrators must be able to block campsites for specified date ranges.

Examples:

- Maintenance.
- Construction.
- Private events.
- Seasonal closures.
- Weather-related closures.
- Administrative use.

Campsite blocks must include:

- Campsite.
- Start date.
- End date.
- Reason.
- Internal notes.
- Created-by user.
- Creation timestamp.

Blocked campsites must not appear as available.

Maintenance blocks must participate in database-enforced occupancy constraints.

If a proposed block conflicts with an existing reservation, reject the operation and require authorized staff to resolve the conflict.

Never silently cancel or override an existing reservation.

---

## 15. Camper-Facing Website

Create a responsive interface optimized for desktop and mobile browsers.

Use Django templates, Bootstrap, HTMX, and vanilla JavaScript.

### 15.1 Public Pages

- Homepage.
- Campground information.
- Campsite listing.
- Campsite details.
- Login.
- Registration.
- Password recovery.
- Campground rules.
- Reservation policies.
- Contact information.

Public availability visibility must be configurable.

Do not disclose private camper information on public pages.

Reservation creation requires an authenticated and authorized account.

### 15.2 Authenticated Camper Pages

- Personal dashboard.
- Find a campsite.
- Availability search.
- Interactive campground map.
- Campsite details.
- Reservation form.
- Reservation confirmation.
- Upcoming reservations.
- Reservation history.
- Reservation details.
- Account settings.
- Security settings.
- Notification center.

### 15.3 Camper Dashboard

Display:

- Upcoming reservations.
- Reservation confirmation numbers.
- Check-in and check-out dates.
- Reservation status.
- Campsite details.
- Available reservation actions.
- Recent notifications.

### 15.4 User Interface Requirements

- Responsive navigation.
- Mobile-friendly forms.
- Clear error and success messages.
- Loading indicators for HTMX requests.
- Accessible form labels.
- Confirmation dialogs for destructive actions.
- Pagination.
- Consistent visual styling.
- Accessible contrast.
- Keyboard navigation.
- Optional dark mode.

Provide server-rendered fallbacks for essential functionality where practical.

Never sacrifice server-side security for frontend usability.

Do not include sensitive data in hidden HTML elements, data attributes, or JavaScript objects unnecessarily.

---

## 16. Interactive Campground Map

Implement an interactive campground map using SVG.

Do not use Google Maps, Mapbox, or external mapping services.

### 16.1 Map Statuses

Use accessible labels and colors:

- Green: available.
- Red: reserved.
- Gray: inactive or unavailable.
- Orange: maintenance.
- Blue: selected.

Users must be able to:

- Select check-in and check-out dates.
- Filter campsite types.
- Filter amenities.
- View availability.
- Select campsites.
- View campsite information.
- Begin reservations.

The map must never reveal other campers' identities or private reservation details.

### 16.2 Map Security

Treat SVG as potentially executable content.

Prefer a controlled campground map representation that generates safe SVG from validated data.

Do not allow unrestricted raw SVG markup to be inserted into rendered HTML.

If SVG uploads are implemented:

- Use a restrictive sanitization allowlist.
- Remove executable content.
- Remove event-handler attributes.
- Remove embedded scripts.
- Remove foreignObject elements.
- Remove external resource references.
- Remove unsafe URL schemes.
- Prevent external XML entity resolution.
- Enforce file size and complexity limits.
- Validate sanitized output.

Do not rely exclusively on file extensions or MIME types.

If SVG uploads cannot be securely implemented, use a safer controlled map format instead.

### 16.3 Map Administration

Authorized administrators should be able to:

- Configure campground maps.
- Associate map locations with campsites.
- Modify campsite display identifiers.
- Enable or disable map display.

Provide a sample campground map for development.

Provide an accessible campsite list as an alternative.

---

## 17. Reservation Calendar

Implement a calendar for authorized staff and administrators.

Support:

- Month view.
- Week view.
- Date navigation.
- Campsite filtering.
- Reservation status filtering.
- Maintenance block visibility.
- Authorized reservation detail access.

Implement a campsite occupancy grid displaying campsites as rows and dates as columns.

Use Django templates, CSS, HTMX, and JavaScript.

Do not introduce paid calendar dependencies.

Do not expose private reservation information through public calendar feeds or unauthenticated endpoints.

---

## 18. Administrative Dashboard

Use Django Admin for internal model management where appropriate.

Also implement a dedicated staff dashboard for daily campground operations.

### 18.1 Administrative Security

Administrative interfaces are high-value attack surfaces.

Require:

- Authentication.
- Appropriate administrative permissions.
- Mandatory MFA.
- Secure sessions.
- Recent reauthentication for sensitive actions.
- Rate limiting.
- Audit logging.
- Appropriate network access restrictions.

Prefer restricting sensitive system administration interfaces to an approved private management network or VPN where practical.

Do not rely on changing the administrative URL as a security control.

Ensure Django Admin cannot bypass reservation services, security policies, or authorization rules.

Restrict direct model editing and bulk actions where they could circumvent required business logic or auditing.

### 18.2 Dashboard Metrics

Display:

- Total campsites.
- Occupied campsites.
- Available campsites.
- Blocked campsites.
- Today's arrivals.
- Today's departures.
- Upcoming reservations.
- Pending reservations.
- Pending account approvals.
- Active campers.
- Occupancy percentage.

### 18.3 Administrative Functions

- View reservations.
- Search reservations.
- Filter reservations.
- Create reservations on behalf of campers.
- Modify reservations.
- Cancel reservations.
- Approve reservations.
- Check campers in.
- Check campers out.
- Manage maintenance blocks.
- Manage campsites.
- Manage campers.
- Approve registrations.
- Manage invitation codes.
- Configure campground settings.
- Review audit logs.
- Export authorized data.

### 18.4 Reports

Support authorized CSV exports for:

- Reservation history.
- Upcoming reservations.
- Camper information.
- Campsite occupancy.
- Campsite utilization.
- Arrivals.
- Departures.

Protect exports against spreadsheet formula injection.

Apply appropriate field-level and object-level authorization.

Do not export unnecessary personal information.

Audit access to sensitive exports.

Never include password hashes, MFA secrets, recovery tokens, credentials, or other security-sensitive data.

---

## 19. Campground Configuration and Branding

Create administrator-configurable settings for:

- Campground name.
- Campground logo.
- Address.
- Contact phone number.
- Contact email address.
- Website description.
- Homepage welcome message.
- Campground rules.
- Reservation policies.
- Timezone.
- Registration mode.
- Permitted email verification settings.
- Primary brand color.
- Secondary brand color.
- Campground map.
- Maintenance announcements.

Do not hardcode campground branding.

Validate all configuration inputs.

Treat administrator-provided content as potentially untrusted.

Prefer plain text or safely rendered Markdown over unrestricted HTML.

Sanitize rich text if supported.

Do not permit configuration fields to introduce executable JavaScript, arbitrary CSS, unsafe external resources, or security-sensitive HTML.

---

## 20. Notifications

Implement a local in-app notification system.

### 20.1 Notification Events

- Account registration.
- Account approval.
- Reservation creation.
- Reservation approval.
- Reservation modification.
- Reservation cancellation.
- Upcoming reservation reminder.
- Campground announcements.

Users should be able to:

- View their notifications.
- Mark notifications as read.
- Mark all notifications as read.
- View unread counts.

Enforce object-level authorization for every notification operation.

### 20.2 Optional Email

Support standard SMTP.

Do not integrate managed email APIs such as:

- SendGrid.
- Mailgun.
- Amazon SES.

Support self-hosted or existing approved SMTP infrastructure.

Protect SMTP credentials through the secrets management system.

Require appropriate TLS and certificate verification.

Do not disable SMTP certificate verification.

Prevent email header injection.

Do not include unnecessary personal information in emails.

Never include passwords or administrative secrets in email messages.

### 20.3 Operation Without SMTP

The application must function without SMTP.

When SMTP is disabled:

- In-app notifications must remain functional.
- Email-dependent verification must not be presented as operational.
- Self-service email password recovery must be disabled.
- Secure administrator-assisted recovery must remain available.
- Registration eligibility must follow the approved production security policy.

Do not silently disable a required verification control merely because SMTP fails.

### 20.4 Scheduled Tasks

Use Django management commands with host cron or systemd timers.

Scheduled tasks must be:

- Idempotent.
- Appropriately logged.
- Concurrency-safe.
- Restricted to necessary permissions.
- Protected against repeated execution.

Do not introduce Redis or Celery without a demonstrated requirement and appropriate review.

---

## 21. Application Security Controls

### 21.1 Input Validation

Validate every untrusted input.

This includes:

- Form fields.
- URL parameters.
- Query parameters.
- HTTP headers.
- Cookies.
- JSON payloads.
- Uploaded files.
- Administrative input.
- Imported data.
- Database content originating from users.

Use allowlists where practical.

Enforce appropriate data types, sizes, formats, and business rules.

Do not rely on client-side validation.

### 21.2 Cross-Site Scripting

Prevent reflected, stored, and DOM-based XSS.

Requirements:

- Keep Django template autoescaping enabled.
- Avoid unsafe use of mark_safe.
- Avoid unrestricted HTML rendering.
- Avoid unsafe innerHTML usage.
- Avoid inline executable JavaScript.
- Escape content according to its output context.
- Sanitize supported rich text.
- Validate user-controlled URLs.
- Restrict script execution through CSP.

Any use of explicitly unsafe rendering functions requires careful review and justification.

### 21.3 Content Security Policy

Implement a restrictive Content Security Policy.

Target a policy based on:

- Locally hosted scripts.
- Locally hosted stylesheets.
- Locally hosted fonts.
- Approved image sources.
- Same-origin connections.
- No plugin or object execution.
- Restricted framing.
- Restricted base URLs.
- Restricted form destinations.

Avoid unsafe-inline and unsafe-eval for scripts.

Use appropriate nonces or hashes where necessary.

Configure HTMX to prevent unnecessary evaluation of dynamic scripts and execution of scripts returned in responses.

Design the frontend to work with restrictive CSP rather than weakening CSP for frontend convenience.

Any proposed CSP relaxation requires explicit approval.

### 21.4 CSRF Protection

Keep Django CSRF middleware enabled.

All state-changing requests must require appropriate CSRF validation.

Ensure HTMX requests include valid CSRF tokens.

Do not use GET requests for state-changing operations.

Do not use csrf_exempt as a convenience workaround.

Any exception requires documented justification and explicit approval.

### 21.5 SQL Injection

Use Django ORM and parameterized queries.

Do not construct SQL statements by concatenating user input.

Raw SQL must be:

- Necessary.
- Parameterized.
- Reviewed.
- Documented.
- Tested appropriately.

### 21.6 Server-Side Request Forgery

Avoid server-side fetching of user-supplied URLs.

If external fetching becomes necessary:

- Require architectural and security review.
- Restrict protocols.
- Restrict destinations.
- Validate redirects.
- Prevent access to internal services.
- Prevent access to loopback and link-local addresses.
- Prevent access to cloud metadata endpoints.
- Account for DNS rebinding.

Do not introduce unrestricted server-side URL fetching.

### 21.7 Open Redirects

Validate authentication and navigation redirect destinations.

Do not allow arbitrary user-controlled external redirects.

Use Django's supported URL safety mechanisms.

### 21.8 HTTP Security Headers

Configure appropriate headers, including:

- Content-Security-Policy.
- Strict-Transport-Security for approved HTTPS production deployments.
- X-Content-Type-Options.
- Referrer-Policy.
- Permissions-Policy.
- Frame restrictions through CSP and appropriate compatibility headers.

Ensure Traefik and Django header configuration do not conflict.

Do not enable unnecessary browser permissions.

### 21.9 HTTPS and Transport Security

Require HTTPS for production.

Use modern supported TLS versions and explicit secure Traefik TLS settings.

Do not disable certificate validation.

Do not permit insecure production fallback to HTTP.

Automatically redirect public HTTP requests to HTTPS where applicable.

Do not transmit authentication credentials over unencrypted connections.

Use an appropriate trusted certificate authority.

For isolated internal deployments, document the use of a properly trusted internal certificate authority.

Protect TLS private keys and certificate management storage.

### 21.10 Proxy Security

Configure trusted forwarded headers carefully.

The application must trust forwarded information only from the intended reverse proxy.

Prevent direct external access to Gunicorn.

Validate host headers.

Configure explicit allowed hosts.

Configure explicit trusted CSRF origins.

Do not use wildcard production host or origin configuration.

### 21.11 Caching

Do not publicly cache authenticated content or sensitive responses.

Ensure cache behavior cannot expose one camper's private information to another camper.

Account for HTMX request variations when caching responses.

Use appropriate cache-control headers for sensitive pages.

### 21.12 Error Handling

Production error responses must not expose:

- Stack traces.
- Database queries.
- Credentials.
- Environment variables.
- Filesystem paths.
- Internal hostnames.
- Authentication details.
- Sensitive configuration.
- Dependency internals.

Return generic user-facing error messages.

Log diagnostic details securely and redact sensitive information.

Disable Django DEBUG in production.

### 21.13 Resource Exhaustion Protection

Implement reasonable limits for:

- Request body size.
- File uploads.
- Image dimensions.
- Authentication attempts.
- Registration attempts.
- Availability searches.
- Reservation attempts.
- Report generation.
- Pagination.
- Session creation.
- Concurrent expensive operations.

Avoid unrestricted database queries driven by user input.

Do not reduce authentication or cryptographic protections to address performance concerns.

---

## 22. Secure File Uploads

All uploaded files must be considered untrusted.

Implement:

- Allowed file-type validation.
- File signature validation.
- File size limits.
- Image dimension limits.
- Randomized storage names.
- Path traversal prevention.
- Safe filesystem permissions.
- Appropriate content types.
- Appropriate Content-Disposition behavior.
- Metadata removal where practical.
- Image decompression limits.
- Secure image processing.

Prefer decoding and re-encoding supported raster images rather than serving original user-provided image content.

Do not allow arbitrary executable files.

Do not allow uploaded HTML or JavaScript.

Do not permit uploaded files to overwrite application code, static assets, or configuration.

Do not store uploads in executable application directories.

Separate public media from private media.

Private media must require authorization before retrieval.

Do not allow public directory listing.

Evaluate isolated media origins and locally hosted malware scanning where justified by the supported upload types and threat model.

---

## 23. Database Security

### 23.1 Database Access

PostgreSQL must not be publicly accessible.

Use:

- Private container networking.
- Strong generated credentials.
- SCRAM-SHA-256 authentication.
- Restricted database roles.
- Least-privileged permissions.
- Appropriate connection security.

Do not use the PostgreSQL superuser as the application's runtime database account.

### 23.2 Database Roles

Separate roles where practical:

- Database administration role.
- Migration role.
- Application runtime role.
- Backup role.

The application runtime role should have only the permissions necessary for normal application operations.

Do not grant unnecessary schema modification, role management, or extension management privileges.

Use a separate controlled migration process for schema changes.

### 23.3 Database Integrity

Use database-level constraints for:

- Required relationships.
- Unique identifiers.
- Valid dates.
- Valid occupancy.
- Appropriate uniqueness.
- Reservation overlap prevention.
- Other critical data integrity requirements.

Do not remove integrity constraints as a workaround for application errors.

### 23.4 Sensitive Data

Minimize collected personal information.

Do not collect unnecessary sensitive information.

Do not store:

- Credit card numbers.
- Government identification numbers.
- Financial account information.
- Unnecessary identity documents.

Encrypt sensitive fields requiring recoverable storage, such as MFA secrets.

Use established cryptographic libraries and appropriate key management.

Do not implement custom cryptographic algorithms.

Protect database storage using appropriate host-level storage encryption.

Document the limitations of encryption at rest when the application or host is compromised.

---

## 24. Audit Logging and Monitoring

Implement application-level audit logging.

### 24.1 Audited Events

Record significant events, including:

- Successful and failed authentication.
- Account registration.
- Account approval.
- Account deactivation.
- Password changes.
- Password recovery events.
- MFA enrollment.
- MFA changes.
- Recovery code regeneration.
- Role changes.
- Permission changes.
- Session revocation.
- Reservation creation.
- Reservation modification.
- Reservation cancellation.
- Reservation approval.
- Check-in.
- Check-out.
- Campsite creation.
- Campsite modification.
- Campsite blocking.
- Configuration changes.
- Sensitive report exports.
- Security-related configuration changes.

### 24.2 Audit Record Fields

Include:

- Event identifier.
- Acting user.
- Action.
- Affected object type.
- Affected object identifier.
- Timestamp.
- Relevant previous values.
- Relevant new values.
- Appropriate request context.
- Outcome.

Collect IP addresses only where justified by security requirements and apply documented retention and access policies.

### 24.3 Prohibited Log Content

Never log:

- Plaintext passwords.
- Password hashes.
- API keys.
- Session identifiers.
- Authentication tokens.
- CSRF tokens.
- MFA secrets.
- Recovery codes.
- Invitation secrets.
- SMTP credentials.
- Encryption keys.
- Entire sensitive request bodies.
- Unnecessary personal information.

Redact sensitive URL parameters and headers.

Ensure reverse proxy access logs do not expose password reset tokens or other credentials.

### 24.4 Log Integrity

Audit records must be read-only through normal application and administrative interfaces.

Restrict access to audit logs.

Prevent ordinary application workflows from modifying historical audit records.

Use database permissions or equivalent controls to make audit records append-only for the runtime application where practical.

Consider protected off-host log storage for improved tamper resistance.

Do not claim application logs are tamper-proof against a fully compromised host or privileged database administrator.

### 24.5 Security Monitoring

Provide locally operated monitoring for:

- Excessive failed authentication.
- Repeated account recovery attempts.
- Suspicious administrative activity.
- Repeated authorization failures.
- Service health.
- Backup failures.
- Certificate expiration.
- Resource exhaustion.

Uptime Kuma may be used as an optional self-hosted monitoring service.

Document monitoring and alerting procedures.

---

## 25. Dependency and Supply-Chain Security

Treat every dependency as a potential security risk.

### 25.1 Dependency Selection

Before introducing dependencies:

- Evaluate whether the dependency is necessary.
- Evaluate project maintenance.
- Evaluate security history.
- Evaluate release activity.
- Evaluate known vulnerabilities.
- Evaluate transitive dependencies.
- Evaluate license compatibility.
- Prefer established, maintained projects.
- Prefer minimal dependency trees.

Do not introduce abandoned or unsupported dependencies without explicit approval.

Do not introduce dependencies with known unresolved applicable security vulnerabilities without explicit approval.

### 25.2 Dependency Locking

Commit pyproject.toml and poetry.lock.

Install reproducible dependency versions.

Pin frontend dependency versions.

Maintain an inventory of vendored frontend assets.

Record their versions, trusted origins, and integrity checksums.

Use trusted package registries and official distribution sources.

Do not install arbitrary remote scripts using shell pipelines.

Do not bypass package integrity verification.

### 25.3 Vulnerability Scanning

Implement:

- pip-audit.
- Bandit.
- Gitleaks.
- Trivy or equivalent container scanning.
- Frontend dependency vulnerability review.
- Infrastructure configuration scanning.

Generate a software bill of materials for production releases where practical.

Do not assume the absence of scanner findings proves that the application is secure.

### 25.4 Security Findings

Applicable unresolved critical or high-severity vulnerabilities must block production release unless the project owner explicitly approves a documented exception.

Evaluate medium and low-severity findings based on applicability, exploitability, and impact.

Do not silently suppress findings.

False-positive determinations must include evidence and review.

Security exception records must include scope, rationale, compensating controls, approval, and expiration or review dates.

### 25.5 Security Updates

Document dependency update procedures.

Apply supported security patches promptly.

Evaluate updates for security regressions.

Run applicable validation before production deployment.

Do not blindly deploy automated dependency updates without validation.

---

## 26. Docker and Infrastructure Security

### 26.1 Container Security

Use:

- Supported base images.
- Trusted image sources.
- Pinned image versions and digests where appropriate.
- Minimal production images.
- Multi-stage builds.
- Non-root application users.
- Read-only root filesystems where practical.
- Explicit writable volumes.
- Temporary filesystems where appropriate.
- Restricted Linux capabilities.
- no-new-privileges.
- Appropriate seccomp and host security profiles.
- Resource limits.
- Health checks.
- Graceful shutdown.
- Restart policies.

Document any required exceptions.

Do not:

- Use privileged containers.
- Mount the Docker socket into application containers.
- Mount unnecessary host directories.
- Use unnecessary host networking.
- Disable container security profiles as a workaround.
- Include compilers and development tooling in production images unnecessarily.
- Bake credentials into images.

### 26.2 Host Security

Document production host hardening.

Include:

- Supported Linux operating system.
- Regular security updates.
- Host firewall.
- Restricted SSH access.
- SSH key authentication.
- Disabled direct root SSH login where practical.
- Restricted administrative accounts.
- Appropriate file permissions.
- Host-level storage encryption.
- Time synchronization.
- Backup protection.
- Physical security considerations.

Restrict exposed application network ports to those required for operation.

Do not expose PostgreSQL, Gunicorn, Docker management APIs, or internal monitoring endpoints publicly.

### 26.3 Environment Isolation

Maintain separate development, testing, and production environments.

Development environments must not:

- Use production secrets.
- Connect to production databases by default.
- Contain real production camper information unnecessarily.
- Expose debug functionality publicly.
- Automatically disable security controls.

Use synthetic test data.

Any deviation from production security controls in development must be documented, isolated, justified, and explicitly approved when it potentially lowers security posture.

---

## 27. Production Configuration and Deployment

### 27.1 Docker Compose Services

Provide:

- web.
- db.
- proxy.

Optional services may be introduced only when justified.

Use a controlled one-shot migration process or equivalent deployment mechanism.

Do not permit migration races between application instances.

### 27.2 Persistent Storage

Provide persistent storage for:

- PostgreSQL data.
- Uploaded media.
- Traefik ACME certificate data.
- Approved collected static files.
- Necessary protected application data.

Restrict permissions appropriately.

### 27.3 Example Environment Configuration

Provide a documented .env.example containing non-secret configuration and secret file references.

Example:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=
DJANGO_CSRF_TRUSTED_ORIGINS=

DJANGO_SECRET_KEY_FILE=/run/secrets/django_secret_key

POSTGRES_DB=campground
POSTGRES_USER=campground_app
POSTGRES_PASSWORD_FILE=/run/secrets/database_password

DATABASE_HOST=db
DATABASE_PORT=5432

APP_DOMAIN=
APP_TIME_ZONE=America/New_York

EMAIL_ENABLED=False
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_PASSWORD_FILE=/run/secrets/smtp_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=30
```

These variables are illustrative and must match the actual implemented configuration.

Do not put real credentials into .env.example.

Do not ship insecure default production credentials.

Ensure secret directories, local environment files, generated keys, and backups are excluded from version control and Docker build contexts.

### 27.4 Production Startup Validation

Production startup must verify:

- Required secrets exist.
- Secrets are not known placeholders.
- DEBUG is disabled.
- Allowed hosts are explicitly configured.
- Required HTTPS configuration is present.
- Secure cookies are enabled.
- Database configuration is valid.
- Security middleware is configured.
- Required MFA enforcement is configured.
- Required rate limiting is configured.
- Email-dependent security settings are consistent.
- Insecure development configuration is not active.

Run Django deployment checks.

Fail startup when critical security requirements are not satisfied.

Do not merely log a warning and continue with insecure production settings.

### 27.5 Deployment Documentation

Document a secure deployment procedure covering:

1. Host preparation.
2. Docker installation.
3. Repository retrieval.
4. Configuration.
5. Secret generation.
6. File permissions.
7. Network configuration.
8. Database initialization.
9. Migration execution.
10. Static file collection.
11. Service startup.
12. Initial administrator creation.
13. Mandatory MFA enrollment.
14. HTTPS verification.
15. Security validation.
16. Backup configuration.

Provide separate documentation for public-domain and private-network deployment.

Traefik may use a public certificate authority for trusted HTTPS certificates.

An internal certificate authority may be used for isolated deployments when properly configured and trusted.

---

## 28. Backup and Disaster Recovery

Backups contain sensitive application information and must receive protections equivalent to production data.

### 28.1 Backup Requirements

Provide backup scripts using PostgreSQL pg_dump and appropriate filesystem backup mechanisms.

Include:

- Database contents.
- Uploaded media.
- Necessary application configuration.
- Required recovery material handled separately where appropriate.

Backups must:

- Be encrypted.
- Use restrictive permissions.
- Support timestamped naming.
- Support configurable retention.
- Be integrity-checked.
- Be protected against unauthorized access.
- Be stored outside publicly accessible application directories.
- Support storage on another physical machine or location.

Restic is an acceptable optional backup tool.

Do not store backup encryption passwords alongside encrypted backups without additional protection.

Do not write backup credentials into logs or command output.

### 28.2 Backup Scheduling

Provide documented cron or systemd timer examples.

Support nightly backups.

Document retention policies.

Monitor backup failures.

Do not silently report successful backups when required backup components fail.

### 28.3 Restoration

Provide documented procedures for:

- Restoring PostgreSQL.
- Restoring uploaded media.
- Restoring required configuration.
- Restoring necessary cryptographic material.
- Restoring onto a replacement server.
- Running required migrations.
- Validating application functionality.
- Validating security controls after restoration.

Require explicit confirmation before destructive restoration.

Test restoration using an isolated environment.

Consider the impact of restored historical credentials, account status, sessions, MFA configuration, and recovery tokens.

Invalidate restored authentication sessions and recovery tokens when appropriate.

Document how to respond when cryptographic keys or credentials are suspected of compromise.

---

## 29. Data Privacy

Collect only information necessary to operate the campground reservation system.

Document:

- Personal information collected.
- Reasons for collection.
- Authorized access.
- Retention periods.
- Export procedures.
- Account deactivation procedures.
- Data deletion or anonymization procedures.
- Backup retention.
- Audit log retention.

Do not introduce third-party tracking or analytics without explicit approval.

Do not transmit camper information to external services unnecessarily.

Do not load external resources that unnecessarily disclose camper browsing activity.

Preserve legitimate reservation and audit records according to documented retention requirements.

Support appropriate account deletion or anonymization where compatible with operational and legal obligations.

---

## 30. Development Environment

Provide a development Docker Compose configuration.

Support:

- Django development server.
- Automatic code reload.
- PostgreSQL.
- Local source-code mounting.
- Development logging.
- Synthetic sample data.
- Locally hosted static assets.
- Automated tests.

Support development on Linux and macOS.

Development services should bind to loopback by default where host exposure is necessary.

Do not expose debug endpoints to public or untrusted networks.

Use generated, isolated development credentials.

Do not reuse production credentials.

Do not automatically connect development tools to production resources.

Keep development conveniences from leaking into production configuration.

---

## 31. Sample Data

Provide an idempotent Django management command:

```bash
python manage.py seed_demo_data
```

Generate:

- Approximately 30 sample campsites.
- Sample campsite types.
- Sample amenities.
- A sample campground map.
- Synthetic camper accounts.
- Sample reservations.
- Maintenance blocks.
- Sample configuration.

Include past, current, and future reservations.

Ensure sample data respects database constraints.

Prevent accidental execution against production environments.

Do not create default production users.

Do not include reusable privileged credentials in the repository.

Do not use actual camper information as sample data.

---

## 32. Testing Requirements

Use pytest and pytest-django.

Use PostgreSQL for tests involving database behavior.

Do not substitute SQLite for PostgreSQL-specific tests.

### 32.1 Authentication Tests

Test:

- Successful registration.
- Duplicate usernames.
- Duplicate email addresses.
- Case-insensitive identity uniqueness.
- Invalid registration data.
- Weak passwords.
- Login.
- Logout.
- Password changes.
- Password recovery.
- Account approval.
- Invitation code validation.
- Invitation expiration.
- Invitation usage limits.
- Concurrent invitation redemption.
- Disabled accounts.
- Login rate limiting.
- Registration rate limiting.
- Password recovery rate limiting.
- Account enumeration protections.

### 32.2 MFA Tests

Test:

- MFA enrollment.
- Valid MFA authentication.
- Invalid MFA authentication.
- Recovery code usage.
- Recovery code reuse prevention.
- Mandatory staff and administrator MFA.
- MFA enforcement across administrative endpoints.
- Unauthorized MFA changes.
- MFA reset procedures.
- Relevant session invalidation.

### 32.3 Authorization Tests

Verify:

- Campers cannot view other campers' private data.
- Campers cannot modify other campers' reservations.
- Campers cannot grant themselves privileges.
- Staff cannot perform unauthorized administrative functions.
- Unauthorized users cannot access administrative endpoints.
- Direct URL access does not bypass authorization.
- HTMX requests enforce the same authorization as standard requests.
- Report exports require appropriate permissions.
- Notifications cannot be accessed by other users.
- Private files cannot be accessed without authorization.

### 32.4 Reservation Tests

Test:

- Valid reservation creation.
- Invalid date ranges.
- Zero-night reservations.
- Reservations in the past when prohibited.
- Overlapping reservations.
- Adjacent reservations.
- Reservations for different campsites on the same dates.
- Inventory release after cancellation.
- Maintenance blocks.
- Maximum reservation length.
- Maximum active reservation limits.
- Advance booking limits.
- Cancellation deadlines.
- Modification deadlines.
- Occupancy limits.
- Duplicate submissions.
- Reservation status transitions.
- Pending reservation expiration.
- Staff policy overrides.

### 32.5 Concurrency Tests

Use separate database connections to test:

- Simultaneous overlapping reservations.
- Reservation and maintenance-block conflicts.
- Concurrent reservation modifications.
- Concurrent account reservation-limit enforcement.
- Concurrent invitation redemption.
- Duplicate submissions.
- Transaction rollback behavior.

Verify that database constraints remain authoritative.

### 32.6 Security Tests

Test protections against:

- Unauthorized object access.
- Privilege escalation.
- CSRF.
- Reflected XSS.
- Stored XSS.
- Unsafe redirects.
- Session fixation.
- Invalid session reuse.
- Malicious file uploads.
- Path traversal.
- CSV formula injection.
- Unsafe SVG content.
- Invalid host headers.
- Spoofed forwarded headers.
- Excessive request sizes.
- Sensitive information disclosure.
- Authentication rate-limit bypasses.
- MFA bypasses.
- Unauthorized administrative actions.
- Sensitive information appearing in logs.

### 32.7 Production Configuration Tests

Verify:

- DEBUG is disabled.
- Missing secrets prevent startup.
- Placeholder secrets prevent startup.
- Production cookies are secure.
- Required middleware is enabled.
- Required security headers are present.
- HTTPS enforcement is correctly configured.
- Wildcard production hosts are rejected.
- Insecure configuration combinations are rejected.
- Development credentials are not accepted as production defaults.

### 32.8 Integration Tests

Test complete workflows:

1. Register an account.
2. Complete required verification or approval.
3. Log in.
4. Search campsite availability.
5. Select a campsite.
6. Create a reservation.
7. View the reservation.
8. Cancel the reservation.
9. Confirm inventory is released.

Also test privileged administrative workflows with mandatory MFA.

### 32.9 Security Regression Tests

Every corrected security vulnerability should receive a regression test where practical.

Security-related tests must not be:

- Deleted to make CI pass.
- Weakened to accommodate insecure implementations.
- Silently skipped.
- Reclassified as irrelevant without documented evidence.

Aim for at least 85% meaningful test coverage.

Prioritize critical security and business logic paths.

Coverage percentage does not replace security validation.

---

## 33. Code Quality

Follow established Django development practices.

Requirements:

- Meaningful naming.
- Python type hints where practical.
- Documentation for complex logic.
- Focused views.
- Centralized reservation services.
- Centralized policy enforcement.
- Reusable authorization checks.
- Server-side forms and validation.
- Appropriate database indexes.
- Atomic transactions.
- Modular templates.
- Minimal dependency coupling.

Use Ruff for linting and formatting.

Use structured logging with sensitive-data redaction.

Avoid custom implementations of:

- Password hashing.
- Session management.
- Cryptographic primitives.
- Authentication protocols.
- Token generation.
- CSRF protection.

Prefer established, reviewed framework functionality.

---

## 34. Continuous Integration and Security Gates

Create CI workflows supporting local reproducibility.

CI should perform:

- Dependency installation.
- Django system checks.
- Migration consistency checks.
- Ruff linting.
- Ruff formatting checks.
- Automated tests.
- Test coverage reporting.
- Bandit security analysis.
- Python dependency auditing.
- Secret scanning.
- Container vulnerability scanning.
- Docker build validation.
- Docker Compose validation.
- Production configuration validation.

### 34.1 CI Security

CI workflows must:

- Use minimum necessary permissions.
- Avoid production credentials.
- Avoid unrestricted access to repository secrets.
- Avoid executing untrusted code with privileged credentials.
- Pin third-party actions to reviewed immutable revisions where practical.
- Protect generated artifacts containing sensitive information.
- Avoid exposing secrets through logs.
- Require appropriate review for changes to security workflows.

### 34.2 Release Security Gates

Production release must be blocked when:

- Critical security tests fail.
- Known applicable high or critical vulnerabilities remain unresolved without explicit approved exceptions.
- Secret scanning detects unresolved secrets.
- Database reservation integrity tests fail.
- Required authorization tests fail.
- Required MFA enforcement fails.
- Production configuration validation fails.
- Security-affecting changes lack required approval.

Do not bypass release security gates to meet development deadlines.

---

## 35. Security Documentation

Maintain the following security documentation.

### SECURITY.md

Document:

- Supported versions.
- Vulnerability reporting procedures.
- Responsible disclosure process.
- General security commitments.
- Supported security update procedures.

### docs/security.md

Document:

- Security architecture.
- Authentication controls.
- Authorization controls.
- MFA requirements.
- Session controls.
- Secrets management.
- Database security.
- Container security.
- Network security.
- Deployment hardening.
- Monitoring.
- Security validation procedures.

### docs/threat-model.md

Document:

- Assets.
- Trust boundaries.
- Attack surfaces.
- Threats.
- Mitigations.
- Residual risks.

### docs/security-decisions.md

Document security-related architectural decisions.

Each security-sensitive decision should include:

- Decision identifier.
- Date.
- Description.
- Alternatives.
- Security impact.
- Justification.
- Residual risks.
- Approval status.
- Approving party when applicable.
- Review date.
- Rollback plan when appropriate.

Do not fabricate approval.

### docs/incident-response.md

Document procedures for:

- Suspected account compromise.
- Administrative account compromise.
- Secret leakage.
- Database compromise.
- Unauthorized access.
- Malicious uploads.
- Suspicious reservation activity.
- Container compromise.
- Host compromise.
- Backup compromise.
- Vulnerable dependency discovery.

Include:

- Identification.
- Containment.
- Credential rotation.
- Session revocation.
- Evidence preservation.
- Remediation.
- Recovery.
- Post-incident review.

### docs/dependency-inventory.md

Document:

- Backend dependencies.
- Frontend dependencies.
- Container images.
- Versions.
- Sources.
- Security considerations.
- Update procedures.

---

## 36. General Documentation

Create a comprehensive README covering:

- Project overview.
- Features.
- Technology stack.
- Architecture.
- Development setup.
- Production deployment.
- Environment configuration.
- Secret generation.
- Database migrations.
- Initial administrator creation.
- MFA enrollment.
- Sample data.
- Automated tests.
- Security checks.
- Code formatting.
- Backup procedures.
- Restoration procedures.
- Application updates.
- Troubleshooting.

Create additional documentation covering:

- Architecture.
- Administration.
- Deployment.
- Backup and restoration.
- Security.
- Threat modeling.
- Incident response.
- Dependency management.

Documentation must not contain actual production secrets.

Troubleshooting instructions must never recommend disabling security controls as a convenience workaround.

---

## 37. Explicitly Out of Scope

Do not implement the following unless explicitly requested:

- Online payment processing.
- Credit card storage.
- Stripe.
- PayPal.
- Subscription billing.
- Dynamic campsite pricing.
- External booking platform integrations.
- Native iOS applications.
- Native Android applications.
- Social media authentication.
- External OAuth providers.
- Managed cloud services.
- Managed email APIs.
- SMS notification providers.
- Kubernetes.
- Microservices.
- AI-powered application features.
- Third-party analytics.
- Public application APIs without an approved requirement.

Do not unnecessarily complicate the application to accommodate speculative future features.

---

## 38. Implementation Phases

### Phase 0 — Security Architecture

Before major implementation:

- Review repository contents.
- Identify application assets and trust boundaries.
- Create the initial threat model.
- Establish the security architecture.
- Define the secrets management approach.
- Define the authentication model.
- Define the permission model.
- Define database roles.
- Define production network boundaries.
- Define dependency security requirements.
- Establish security scanning.
- Document security-related assumptions.
- Identify any decisions requiring explicit approval.

Do not proceed with a security-reducing decision without approval.

### Phase 1 — Project Foundation

- Initialize Poetry.
- Configure Django.
- Configure PostgreSQL.
- Create the custom user model.
- Configure environment-specific settings.
- Implement secrets management.
- Create Docker configurations.
- Configure Traefik.
- Establish testing infrastructure.
- Establish linting.
- Establish CI security scanning.
- Create initial documentation.

### Phase 2 — Authentication and Authorization

- Implement self-service registration.
- Implement registration modes.
- Implement invitation codes.
- Implement account approval.
- Implement login and logout.
- Implement password recovery.
- Implement Argon2id.
- Implement MFA.
- Implement session security.
- Implement rate limiting.
- Implement roles and permissions.
- Implement authentication security tests.

### Phase 3 — Campground and Campsites

- Implement campground configuration.
- Implement campsite models.
- Implement campsite types.
- Implement amenities.
- Implement secure image uploads.
- Configure administrative management.
- Implement relevant security tests.

### Phase 4 — Reservation Engine

- Implement reservation models.
- Implement unified occupancy.
- Implement PostgreSQL exclusion constraints.
- Implement availability queries.
- Implement booking policies.
- Implement maintenance blocks.
- Implement centralized reservation services.
- Implement status transitions.
- Implement transaction safety.
- Implement concurrency tests.
- Implement authorization tests.

Prioritize database correctness and security before extensive frontend implementation.

### Phase 5 — Camper Interface

- Implement homepage.
- Implement camper dashboard.
- Implement campsite listing.
- Implement availability search.
- Implement campsite details.
- Implement reservation forms.
- Implement reservation confirmations.
- Implement reservation management.
- Implement responsive navigation.
- Implement HTMX interactions.
- Validate CSP compatibility.
- Validate CSRF enforcement.
- Validate object-level authorization.

### Phase 6 — Interactive Map and Calendar

- Implement a secure campground map.
- Implement campsite selection.
- Implement availability indicators.
- Implement date filtering.
- Implement reservation calendar.
- Implement occupancy grid.
- Validate map sanitization and privacy protections.

### Phase 7 — Administrative Interface

- Implement operational dashboard.
- Implement camper management.
- Implement reservation management.
- Implement arrivals and departures.
- Implement check-in and check-out.
- Implement configuration management.
- Implement reports and exports.
- Validate granular permissions.
- Validate mandatory MFA.
- Validate administrative auditing.

### Phase 8 — Notifications and Audit Logging

- Implement in-app notifications.
- Implement optional SMTP.
- Implement scheduled notifications.
- Implement audit logging.
- Implement security event logging.
- Validate secret redaction.
- Validate notification authorization.

### Phase 9 — Production Hardening

- Complete production security configuration.
- Complete host security documentation.
- Complete container hardening.
- Complete backup scripts.
- Complete restore scripts.
- Complete CI workflows.
- Complete security documentation.
- Review dependency security.
- Review authentication security.
- Review authorization security.
- Review application performance.
- Review accessibility.

### Phase 10 — Final Security Review

Perform a comprehensive release security review.

Verify:

- Secrets management.
- Authentication.
- MFA.
- Authorization.
- Session security.
- CSRF protection.
- CSP.
- Input validation.
- File uploads.
- Database integrity.
- Container isolation.
- Network isolation.
- Dependency security.
- Audit logging.
- Backup security.
- Production deployment configuration.
- Security regression tests.

Perform automated security scanning and targeted manual security review in an authorized isolated environment.

Document findings and unresolved risks.

Do not represent the application as independently penetration-tested or certified unless such testing has actually occurred.

Do not consider the application ready for production while release-blocking security findings remain unresolved.

---

## 39. Acceptance Criteria

The application is considered complete only when the following applicable requirements are implemented and verified.

### Functional Requirements

- Docker Compose deployment works.
- Users can create their own accounts.
- Registration modes are configurable.
- Local username and password authentication works.
- Campers can search campsite availability.
- Campers can create reservations.
- Campers can manage their own reservations.
- Administrators can manage accounts.
- Administrators can manage campsites.
- Staff can manage campground operations.
- Maintenance blocks work.
- Reservation policies are configurable.
- Interactive maps display actual availability.
- Calendar and occupancy views work.
- The application is mobile-friendly.
- In-app notifications work.
- Optional SMTP works when configured.
- Backup and recovery procedures are available.
- Documentation is complete.

### Security Requirements

- No knowingly unauthorized security-reducing decisions have been implemented.
- Required security approvals are documented.
- No unresolved secrets are present in version control.
- Passwords are securely hashed.
- Privileged accounts require MFA.
- Authentication endpoints are rate limited.
- Authorization is enforced server-side.
- Campers cannot access other campers' private information.
- Sessions are securely managed.
- CSRF protection is enforced.
- CSP is restrictive and functional.
- HTTPS is required in production.
- Production cookies are secure.
- Database access is restricted.
- Application runtime database permissions are minimized.
- PostgreSQL is not publicly exposed.
- Gunicorn is not publicly exposed.
- Container privileges are restricted.
- File uploads are securely handled.
- Logs do not expose secrets.
- Sensitive exports are protected.
- Backups are encrypted.
- Dependency security scanning is implemented.
- Release-blocking vulnerabilities are resolved or explicitly approved.
- Production configuration fails closed.
- Security regression tests pass.
- Reservation concurrency tests pass.
- Overlapping reservations are prevented at the database level.
- Maintenance blocks participate in occupancy constraints.
- Security documentation is complete.
- Known limitations and residual risks are documented.

No application can be guaranteed free of all vulnerabilities. Completion requires appropriate implementation, validation, and transparent reporting of remaining risks.

---

## 40. Implementation Progress

Maintain:

```text
docs/implementation-progress.md
```

Include:

- Completed phases.
- Current phase.
- Completed functionality.
- Remaining functionality.
- Architectural decisions.
- Security decisions.
- Pending security approvals.
- Known security findings.
- Resolved security findings.
- Known limitations.
- Testing status.
- Deployment status.
- Recommended next steps.

Update this document throughout development.

Do not mark functionality complete unless it is implemented.

Do not mark functionality verified unless appropriate validation has actually been performed.

---

## 41. Final Instructions to Codex

Implement this application as a complete, functional software project.

Begin by reviewing the repository, AGENTS.md, and this specification.

Create an implementation plan and initial threat model.

Proceed through the implementation phases in logical order.

Do not stop after scaffolding or planning.

Prioritize:

1. Security.
2. Data integrity.
3. Correctness.
4. Reliability.
5. Maintainability.
6. Functionality.
7. Performance.
8. User convenience.
9. Development speed.

Security must remain the highest priority.

Never independently make or implement a decision that could potentially weaken the application's security posture.

Any such decision requires explicit project-owner approval before implementation.

When encountering a security conflict:

1. Preserve the existing security control.
2. Investigate secure alternatives.
3. Document the conflict.
4. Request explicit approval if a weaker alternative is being considered.
5. Continue unrelated implementation work where possible.
6. Do not implement the weaker alternative while approval is pending.

Never disable a security control to make functionality work.

Never disable a security control to make tests pass.

Never expose secrets for debugging convenience.

Never introduce insecure temporary workarounds.

Never fabricate test results, security approval, or security compliance.

At the conclusion of each development session, provide:

1. Summary of implemented functionality.
2. Files modified.
3. Dependencies introduced.
4. Database migrations introduced.
5. Architectural decisions.
6. Security improvements.
7. Security-related decisions.
8. Potential security impacts.
9. Pending security approvals.
10. Identified vulnerabilities.
11. Resolved vulnerabilities.
12. Known limitations.
13. Testing and validation status.
14. Commands required for validation.
15. Remaining implementation work.
16. Recommended next steps.

The final product must be a secure, reliable, maintainable, fully self-hosted campground reservation system suitable for real-world use by approximately 100 campers per campground, with verified tenant isolation and measured aggregate capacity.

Security is not an optional feature. Security is a mandatory requirement of every feature.
