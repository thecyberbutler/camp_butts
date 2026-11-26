# Optional Google sign-in

The owner requested Google login and explicitly approved restricted Google egress (SD-027).
All other authentication/security requirements remain in force. Local login is retained.
Google is an external identity dependency; the application and its data remain self-hosted.

## Google console configuration

Use a dedicated **Web application** client for each deployment environment. The AWS test
client has an External audience and **Testing** publishing status. The owner confirmed the
intended test account is configured; personal account identifiers are not copied here.
Use this exact authorized redirect URI, including its final slash:

```text
https://camp-butts-test.thecyberbutler.io/c/georgia-mountain-fairgrounds/accounts/google/login/callback/
```

No JavaScript-origin credential flow, One Tap or refresh/offline access is used. Under the
owner's additional SD-029 approval, new releases request `openid email profile` and
`https://www.googleapis.com/auth/user.phonenumbers.read`. Do not add contacts scopes or
wildcard callback URIs, and do not reuse production secrets in test. Profile pictures and
unrelated fields are discarded; no remote avatar is fetched or embedded.

For the name/phone feature, select the project owning the existing test Web application
client, enable **People API** in APIs & Services, and open **Google Auth Platform → Data Access**.
Retain the OpenID/email permissions and add the name/profile permission (console entry
`https://www.googleapis.com/auth/userinfo.profile`, requested as OIDC `profile`) plus
`https://www.googleapis.com/auth/user.phonenumbers.read`. Keep the External audience in
Testing with intended test users. Google may require verification of sensitive scopes before
production; review the console classification and Google's current requirements.

The client ID, protected client-secret file and exact redirect URI remain unchanged. No new
JavaScript origin or credential is required for this server-side flow. An existing Google
grant may prompt for the added permission; users may leave optional phone access ungranted.
Google audience/publishing settings are separate from local campground registration approval.
If no usable phone is returned, the signup form remains usable with manual optional input.

## Protected file

The owner installed `/opt/camp-butts-test/.secrets/google_oauth.json`, regular file mode 0600,
UID/GID 10001, in the existing protected secret directory. Its JSON maps the campground slug
to exactly `client_id` and `secret`. Never paste its contents into chat, terminals, environment
files, Docker build arguments or version control. Use an interactive non-echoing prompt to
create/replace credentials, never a shell command containing the secret. Startup rejects
invalid/public/symlinked files. The file is mounted only into web, read-only, and is the sole
source of client credentials. Database SocialApp configuration is deliberately unavailable.

Google login is absent unless the selected campground has an entry. Each campground has its
own local accounts and provider links even if the operator registers multiple exact callback
URIs with one client. Dedicated clients per campground reduce rotation/compromise scope.
The OAuth file has a bounded 4096-byte parser; do not silently expand it for large deployments.

## Container deployment

Use the normal digest-locked registry deployment with `-f compose.google.yaml` added **after**
`compose.yaml` and `compose.registry.yaml`. Set `CAMPGROUND_EGRESS_IMAGE` from the published
release lock. Do not change the web container to an Internet-connected network. The overlay
adds an internal `172.30.20.0/28` network and a separate outbound network for Squid only.
Check host/Docker subnet conflicts before installation. Squid has no public port, database
network or credential mount and permits only the fixed web address to CONNECT on port 443
to `oauth2.googleapis.com`, `www.googleapis.com` and `people.googleapis.com`; private/metadata
addresses are denied. Application transport verifies TLS, forbids redirects and additional
query parameters, and permits only token POST, signing-key GET and this exact self-profile GET:
`https://people.googleapis.com/v1/people/me?personFields=phoneNumbers&sources=READ_SOURCE_TYPE_PROFILE`.
No contacts, connections, other users or broader field mask can be requested by this helper.
Access/cache logs and caching are disabled. CSP stays `form-action 'self'`: a local interstitial
performs ordinary browser navigation after the CSRF-protected start.

Apply vendor allauth socialaccount migrations 0001–0006 to every tenant, then reapply runtime
grants and forced RLS. Runtime cannot read client-secret tables, insert/update token rows,
or use their sequences. SELECT/DELETE on token rows supports Django's unlinking cascade.
No token is persisted in the DB, pending signup session or audit records. Collect static
assets before replacing web. Existing database/Traefik base images and security controls
remain unchanged. The AWS first-enable script also creates an encrypted recovery snapshot;
see [snapshot limitations](backup-and-restore.md#google-enablement-snapshot).

## Account behavior and manual acceptance

1. Open the campground's sign-in page and choose **Continue with Google**. Test users must
   belong to the Google console's allowed audience. No Google password is entered into this app.
2. New users review/edit first and last names suggested by the verified Google ID token.
   Optional phone suggestions use the transient access token and the fixed People API
   endpoint. Missing/denied/malformed profile data leaves fields for manual entry. Names are
   bounded to 150 characters without control characters; phone input retains the existing
   32-character validator. Only a bounded primary/first usable number is suggested. This
   never marks the number verified or enables phone login, MFA or account recovery.
   New users complete local required registration details, rules and policy acceptance.
   Georgia Mountain Fairgrounds remains approval-based. The uniform registration response
   does not grant login, approve accounts or assign staff privileges.
3. Existing local accounts are never linked merely because email addresses match. Sign in
   locally, use **Google sign-in**, confirm the local password, and connect the matching
   Google account explicitly. Privileged accounts also require application MFA.
4. After approved account linking/registration, sign in with Google and confirm the expected
   campground dashboard and MFA challenge where applicable. Connection changes revoke old
   sessions. Repeat sign-in after a connection change.
5. Disconnect requires local password reauthentication and a usable recovery path. Do not
   create bypasses for Google-only accounts during provider outages.

Automated tests use locally signed synthetic OIDC assertions, not real credentials. Public
probes validate the start/callback controls but do not complete a human Google consent flow.
Only claim live end-to-end sign-in after a test user actually completes it. Never send the
callback URL, cookies, codes or tokens as troubleshooting evidence; report status only.

## Current test deployment

The current live release is `0.1.0-alpha.20261125-5815b9993895` (interface update). It still
uses the original email-only Google scopes and username-based local login. The email-account
migration and Google profile changes are implemented/tested locally, **not yet deployed**.
Configure the API/consent settings above before the new scanned release and migration-aware
cutover described in `email-identity.md`. The public scope probe in the new source expects
new scopes and should be run only after that deployment.
For the deployed release, the owner-installed protected file was validated in the intended web image, without exposing
its contents. The red test banner remains visible. Automated public start/CSRF/PKCE/nonce
checks and actual runtime database/container/Google-key transport checks passed.
Human Google consent, token exchange and approved-user sign-in are still pending.

## Verification

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh tests/security/test_google_oauth.py tests/security/test_deployment_snapshot.py -q --assert=plain --tb=no --show-capture=no
.venv/bin/python -m scripts.check_google_egress IMAGE_REFERENCE_FROM_RELEASE
SSL_CERT_FILE=/etc/ssl/cert.pem .venv/bin/python scripts/check_public_test.py
.venv/bin/python scripts/check_public_google.py
```

The real proxy test creates disposable private Docker networks and verifies allowed TLS,
wrong-source/host/port rejection, metadata/private address denial, DNS-to-metadata denial and
blocked direct web-side Internet access. Run on a host where `172.30.20.0/28` is unused,
not on the enabled deployment. Public probes make bounded synthetic requests, never approve
an account or create a reservation. Do not publish their raw HTTP responses.

## Rotation and rollback

Rotate credentials in Google's console and atomically replace the protected file, preserving
ownership/mode; recreate web so settings reload. Do not retain a plaintext backup. Update
exact callback registrations when a hostname/slug changes. On incident, disable Google and
detach web from the optional egress network, stop/remove the sidecar, and recreate web with
the base registry configuration. Preserve provider-link tables, tenant data and local auth;
do not reverse additive migrations or remove volumes. Invalidate affected application sessions
separately. Revoke Google credentials if compromised. Recovery of Google-only accounts follows
the existing reviewed operator process. This capability does not satisfy remaining production
release gates, including complete recovery, provider live acceptance and operational review.

## Reviewed upstream references

- [allauth Google provider](https://docs.allauth.org/en/latest/socialaccount/providers/google.html)
- [allauth social-account settings](https://docs.allauth.org/en/latest/socialaccount/configuration.html)
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
- [Google token and email authority guidance](https://developers.google.com/identity/sign-in/web/backend-auth)
- [Squid ACL configuration](https://www.squid-cache.org/Doc/config/acl/)
- [Squid access controls](https://static.squid-cache.org/Doc/config/http_access/)


## Profile data lifecycle and verification limits

Google `sub` remains the provider identity. Name/phone are untrusted editable contact
suggestions, not evidence for account linking, role assignment or mailbox/phone verification.
Existing linked-account sign-ins and explicit connections never fetch phone data or overwrite
local contact fields. Only pending new registration receives suggestions, protected by the
tenant-bound encrypted expiring session. The access/ID token and raw profile response are not
stored. SocialAccount extra data remains limited to email. No consent checkbox is preaccepted.

Automated tests use signed synthetic ID tokens and bounded People responses, including denied
permission, malformed names/numbers, unrequested scopes, TLS failure, XSS escaping and existing
profile non-overwrite. The real proxy test checks verified Google/People TLS and denied private,
metadata, wrong-peer/host/port routes without a real OAuth token. This does not prove Google
Cloud configuration, live personal profile availability or human consent/token exchange.

Additional references: [Google OIDC claims](https://developers.google.com/identity/openid-connect/reference),
[People self-profile fields/scopes](https://developers.google.com/people/api/rest/v1/people/get),
[OAuth scope configuration](https://developers.google.com/identity/protocols/oauth2/scopes),
[sensitive-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification).
