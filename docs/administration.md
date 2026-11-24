# Administration

## First administrator and MFA

Use the normal registration form with a unique password. Registration creates an
unprivileged pending account. On the protected host, after independently verifying
identity, run `setup_roles`, then:

```sh
docker compose exec web python manage.py authorize_account USERNAME \
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
Policy overrides, arbitrary reservation edits, user deactivation UI, invitation management
UI and a complete audit viewer remain backlog items. CSV currently exports occupancy
without camper contact data; formula-like site names are escaped.

## Configuration and invitations

Business policies and plain-text branding are editable by authorized administrators.
Defaults: 1–14 nights, maximum 2 active reservations, 1-day notice, 180-day advance window,
2-day cancellation/modification notice, no simultaneous multi-site bookings, automatic
reservation confirmation, 24-hour holds if approval is enabled. Pending holds always
occupy inventory until resolved or expired. Registration mode defaults to approval;
model/service support open, invitation and disabled modes, but a dedicated mode-management
interface is still required. Do not change security settings through incidental forms.

`create_invitation --actor USERNAME --output /protected/new-file --uses 1 --days 7`
writes a generated invitation to a new 0600 file in a 0700 directory. Store only its
digest in the database. Deliver the secret through an approved private channel. The
application does not log or display it. Expiry and use counts are enforced transactionally.

## Scheduled tasks and retention

Run every five minutes using a dedicated host timer:

```sh
docker compose exec -T web python manage.py expire_reservations
```

Run `clearsessions` daily. Review Axes records and establish bounded retention for IPs
and login-attempt records before production. Audit/contact/reservation retention and
anonymization policy require owner decisions; automated retention is not implemented.
Alert locally on job failures, repeated failed logins, privilege changes, backup failures,
disk exhaustion and certificate renewal failures. Do not dump request bodies for diagnosis.

## Recovery

Without SMTP, self-service reset is denied. A protected operator may use Django's
interactive `changepassword USERNAME` only after independent identity verification;
the password is entered without echo and never sent by email. For privileged users,
password recovery does not remove TOTP. Lost MFA requires an owner-controlled, audited
recovery procedure; there is no web bypass or universal recovery credential. The complete
dual-control lost-MFA recovery procedure remains a production prerequisite.

`seed_demo_data` creates 30 synthetic campsites/types/amenities/map positions only in
development/testing. It does not create passwords. Rich sample reservation/account data
is still pending. Never enable that command in production to simplify setup.
