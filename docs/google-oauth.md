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

No JavaScript-origin credential flow, One Tap, refresh/offline access or profile/photo scope
is used. The browser requests `openid email` only. Do not use wildcard callback URIs or reuse
production secrets in test. Google audience/publishing requirements are separate from local
campground registration approval. Review Google's requirements before changing to production.

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
to `oauth2.googleapis.com` and `www.googleapis.com`; private/metadata addresses are denied.
The application verifies Google's TLS and permits only token POST and signing-key GET paths.
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
2. New users complete local required registration details, rules and policy acceptance.
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

Release `0.1.0-alpha.20261125-3386d5caf5b3` is deployed at the HTTPS callback host above.
The owner-installed protected file was validated in the intended web image, without exposing
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
