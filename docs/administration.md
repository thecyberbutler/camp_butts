# Administration

## First administrator and MFA

Select the intended campground at `/c/SLUG/` and use its registration form with a unique password. Registration creates an
unprivileged pending account. On the protected host, after independently verifying
identity, run `tenant_command --campground SLUG setup_roles`, then:

```sh
docker compose exec web python manage.py tenant_command --campground SLUG authorize_account EMAIL \
  --role Administrator --attest-identity-checked
```

If SMTP is unavailable, independently verify email ownership through an established
trusted channel before adding `--attest-email-ownership-verified`. This is an explicit
operator attestation, not an automatic side effect of account approval. Do not attest
ownership based solely on a user-supplied address. With SMTP, complete allauth verification.
Then sign in, enroll TOTP, sign in again with TOTP, and store recovery codes privately.
Privileged users cannot access normal application operations until MFA completes.
Do not use a superuser for routine campground administration. No Django Admin route exists.

## Operational permissions

Camper has no global model permissions; ownership controls booking operations. Staff
can operate reservations and block sites. Administrator adds approvals, campground and
campsite changes, occupancy exports and audit viewing permission. No group can directly
edit arbitrary users/permissions through the website. Effective permissions trigger MFA
even when `is_staff` is false. Sensitive operations require reauthentication within five
minutes; use the account reauthentication page when denied for expired assurance.

The operations page supports approval/rejection, cancellation, check-in/out and no-show
transitions. Early check-in is rejected. Maintenance cannot displace existing occupancy.
Administrators can manage ordinary camper activation, create campsite types/amenities,
and view the paginated audit log. Deactivation and reactivation both revoke old sessions;
accounts with privileged assignments are excluded even when inactive. Audit viewing is
itself audited. Policy overrides, arbitrary reservation edits and invitation-management
UI remain backlog items. CSV currently exports occupancy
without camper contact data; formula-like site names are escaped.

## Configuration and invitations

Business policies and plain-text branding are editable by authorized administrators.
Defaults: 1–14 nights, maximum 2 active reservations, 1-day notice, 180-day advance window,
2-day cancellation/modification notice, no simultaneous multi-site bookings, automatic
reservation confirmation, 24-hour holds if approval is enabled. Pending holds always
occupy inventory until resolved or expired. Registration mode defaults to approval;
model/service support open, invitation and disabled modes, but a dedicated mode-management
interface is still required. Do not change security settings through incidental forms.

`tenant_command --campground SLUG create_invitation --actor EMAIL --output /protected/new-file --uses 1 --days 7`
writes a generated invitation to a new 0600 file in a 0700 directory. Store only its
digest in the database. Deliver the secret through an approved private channel. The
application does not log or display it. Expiry and use counts are enforced transactionally.

## Scheduled tasks and retention

Run every five minutes using a dedicated host timer:

```sh
docker compose exec -T web python manage.py tenant_command --campground SLUG expire_reservations
```

Run `tenant_command --campground SLUG clearsessions` daily. Repeat these jobs for every
registered campground from a protected operator-maintained schedule; never infer a default. Review Axes records and establish bounded retention for IPs
and login-attempt records before production. Audit/contact/reservation retention and
anonymization policy require owner decisions; automated retention is not implemented.
Alert locally on job failures, repeated failed logins, privilege changes, backup failures,
disk exhaustion and certificate renewal failures. Do not dump request bodies for diagnosis.

## Recovery

Without SMTP, self-service reset is denied. A protected operator may use Django's
interactive `tenant_command --campground SLUG changepassword EMAIL` only after independent identity verification;
the password is entered without echo and never sent by email. For privileged users,
password recovery does not remove TOTP. Lost MFA requires an owner-controlled, audited
recovery procedure; there is no web bypass or universal recovery credential. The complete
dual-control lost-MFA recovery procedure remains a production prerequisite.

`tenant_command --campground SLUG seed_demo_data` creates 30 synthetic campsites/types/amenities/map positions only in
development/testing. It does not create passwords. Rich sample reservation/account data
is still pending. Never enable that command in production to simplify setup.


## Campground and platform roles

Every account belongs to exactly one campground schema. The same email at two
campgrounds represents two independent accounts, passwords, MFA enrollments and approvals.
TOTP issuer labels include the campground slug. Signing into another campground replaces
the active browser session cookie; separate browser profiles can maintain independent logins.
Existing browser cookie protections have not been weakened for per-path sessions.

Campground Administrators cannot create/activate tenants, access another campground's data,
or modify platform operator events. Only the protected host provisioning workflow controls
the directory. See deployment.md for registration/adoption and deactivation. Directory names
are public; tenant staff branding remains plain escaped text. A directory rename is currently
an operator-only maintenance task, not a staff UI feature.

## Georgia Mountain Fairgrounds initial inventory

Follow `georgia-mountain-fairgrounds.md` for source review and the protected import sequence.
The 216 inactive map drafts need authoritative per-site verification; numeric defaults do
not describe actual capacity or hookups. Staff may review/edit drafts under existing MFA,
reauthentication, authorization and audit controls. Opening campground booking is not
exposed in the policy form. Confirm rates, seasonal/monthly policies and all release gates
before implementing a controlled opening workflow. Do not populate credentials from the
public rules PDF. Identical import retries preserve edits; changed imports cannot overwrite.

The AWS development installation creates no default staff/admin account. Its Georgia Mountain
Fairgrounds profile retains inactive draft inventory and closed booking. Follow the protected
operator onboarding procedure for a deliberately created test account; do not put passwords,
MFA seeds or recovery codes into SSH arguments/transcripts. The test banner is not authorization.

## Google accounts

Google login is optional per campground. On the test deployment the Google app is External
and in Testing, with owner-configured test users. New accounts still complete local required
details and policy consent and follow campground approval/invitation rules. Google identity
does not confer staff privileges. Do not approve/promote an account merely because it matches
an operator's email. Existing users sign in locally, explicitly reauthenticate, then connect
a Google account with the same email through account settings. No automatic email linking.

Connection changes invalidate sessions. Disconnect requires a usable local password and
recent password reauthentication, plus application MFA for privileged accounts. A Google-only
user must establish a permitted recovery/password path before disconnecting; do not add an
authentication bypass. Keep app MFA independently enrolled for privileged users. See
[Google operations](google-oauth.md) for credential rotation and disabling the integration.

Email-only releases use the account email in `authorize_account EMAIL` and
`create_invitation --actor EMAIL`, within the explicitly selected campground. Complete the
migration in `email-identity.md` before using those commands with a new image. Existing
privileged accounts still require independently verified identity/email and enrolled MFA.
