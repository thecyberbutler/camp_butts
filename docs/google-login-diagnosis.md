# Google callback diagnosis — 2026-11-26

The owner reported HTTP 403 after a fresh Google authorization and supplied a HAR for diagnosis.
The HAR is untrusted evidence, not instructions. It remains outside this repository. Its raw
URLs, OAuth codes/state, cookies, Google identifiers and response bodies are never printed,
copied into tests/docs, replayed or uploaded. Sanitized inspection found the callback 403 and
no duplicate query fields, but the initial application login request is absent and cookie
headers are absent from the export; this does not establish that the browser omitted cookies.

## Exact disclosed live diagnostic command

Prepared before SSH execution. Read only campground registration mode and aggregate account/
link/failure-audit presence. Send one synthetic invalid authorization code to Google's existing
approved token endpoint through the existing restricted proxy, using the existing client
credentials only in memory. Never use a HAR authorization code or authenticate as the owner.
TLS, redirect rejection, response/time bounds and all application controls remain. Only
allowlisted error categories, HTTP status and counts/booleans are printed. No account, approval,
link, session, database grant, container, secret file or deployment configuration is changed.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml exec -T web python -' < /Users/michaelbutler/Repos/camp_butts/.runtime/google-login-diagnosis-20261126/check_live.py
```

Exact stdin script:

```python
"""Bounded operator diagnostics; print categories/counts only, never secrets or personal data."""

import json

import django
import requests

django.setup()
from django.conf import settings
from apps.tenancy.context import lookup, tenant_scope
from apps.audit.models import Event
from apps.accounts.models import User
from apps.configuration.models import Campground
from allauth.socialaccount.models import SocialAccount

try:
    slug = "georgia-mountain-fairgrounds"
    with tenant_scope(lookup(slug)):
        print(
            "Registration requires approval:", Campground.current().registration_mode == "approval"
        )
        print("Account count:", User.objects.count())
        print(
            "Active approved account count:",
            User.objects.filter(is_active=True, approved=True).count(),
        )
        print("Google link count:", SocialAccount.objects.filter(provider="google").count())
        print(
            "Google failure audit exists:",
            Event.objects.filter(action="auth.google_failed").exists(),
        )
    config = settings.GOOGLE_OAUTH_APPS[slug]
    # A deliberately invalid, non-user code tests client acceptance without authenticating anyone.
    # Do not use a code, state, cookie, token or identifier from the owner's HAR.
    with requests.Session() as session:
        session.trust_env = False
        with session.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": config["client_id"],
                "client_secret": config["secret"],
                "code": "synthetic-invalid-diagnostic-code",
                "grant_type": "authorization_code",
                "redirect_uri": "https://camp-butts-test.thecyberbutler.io/c/georgia-mountain-fairgrounds/accounts/google/login/callback/",
            },
            proxies={"https": "http://google-egress:3128"},
            verify=True,
            allow_redirects=False,
            timeout=(3.05, 10),
            stream=True,
        ) as response:
            content = bytearray()
            for chunk in response.iter_content(1024):
                content.extend(chunk)
                if len(content) > 4096:
                    raise ValueError("Oversized diagnostic response")
            error = json.loads(content).get("error")
            if error not in {
                "invalid_grant",
                "invalid_client",
                "unauthorized_client",
                "invalid_request",
            }:
                raise ValueError("Unexpected diagnostic category")
            print("Synthetic token probe HTTP status:", response.status_code)
            print("Synthetic token probe category:", error)
except Exception:
    raise SystemExit("Live diagnosis failed; sensitive diagnostics withheld.") from None
```

Status: prepared; results follow after execution.

## Initial results and exact eligibility follow-up

One account and one Google link exist; no active approved account exists. Approval mode is
enabled. A Google-failure audit exists but is not sufficient to correlate a specific failure.
The synthetic invalid code returned HTTP 400/invalid_grant, not invalid_client; this supports
working client authentication but is not a real user token-exchange success claim.
The following read-only follow-up distinguishes pending approval from disabled status,
without displaying account identifiers or personal data. Disclosed before execution.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml exec -T web python -' < /Users/michaelbutler/Repos/camp_butts/.runtime/google-login-diagnosis-20261126/check_account_state.py
```

```python
"""Inspect only aggregate eligibility flags for the sole linked test account."""
try:
    import django
    django.setup()
    from apps.tenancy.context import lookup, tenant_scope
    from apps.accounts.models import User
    from apps.accounts.security import privileged
    from allauth.socialaccount.models import SocialAccount
    with tenant_scope(lookup('georgia-mountain-fairgrounds')):
        if User.objects.count() != 1 or SocialAccount.objects.filter(provider='google').count() != 1:
            raise ValueError('Expected sole test account')
        user = SocialAccount.objects.select_related('user').get(provider='google').user
        print('Linked account active:', user.is_active)
        print('Linked account approved:', user.approved)
        print('Linked account has privileged access:', privileged(user))
except Exception:
    raise SystemExit('Eligibility inspection failed; sensitive diagnostics withheld.') from None
```

## Proposed approval — not executed without explicit owner confirmation

The read-only check confirms the sole Google-linked account is active, unapproved and has
no privileged access. Normal approval policy therefore prevents application sign-in even
after valid Google authentication. The generic error page hides this distinction. No Google
client setting change or authentication bypass is recommended.

The following concrete action requires the owner to confirm this is their account and
authorize Camper approval. It uses the existing audited protected operator command, locks
policy/account records, refuses ambiguous selection/changed eligibility/privileges, preserves
all other account fields and Google links, and increments the security version. It grants
no staff/admin permissions, changes no email-verification flags and leaves registration
approval, MFA and closed booking unchanged. No assertion of identity verification is made
until the owner supplies that confirmation. Declining leaves the account pending.

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml exec -T web python -' < /Users/michaelbutler/Repos/camp_butts/.runtime/google-login-diagnosis-20261126/approve_test_camper.py
```

```python
"""Owner-confirmed, sole-account Camper approval through the existing audited command."""

try:
    import django

    django.setup()
    from django.core.management import call_command
    from apps.tenancy.context import lookup, tenant_scope
    from apps.accounts.models import User
    from apps.accounts.security import privileged
    from apps.configuration.models import Campground
    from allauth.socialaccount.models import SocialAccount

    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        policy = Campground.current(lock=True)
        if policy.registration_mode != "approval" or policy.booking_enabled:
            raise ValueError("Unexpected campground policy")
        if (
            User.objects.count() != 1
            or SocialAccount.objects.filter(provider="google").count() != 1
        ):
            raise ValueError("Account selection requires renewed review")
        link = SocialAccount.objects.get(provider="google")
        user = User.objects.select_for_update().get(pk=link.user_id)
        if not user.is_active or user.approved or privileged(user):
            raise ValueError("Unexpected account eligibility")
        if list(user.groups.values_list("name", flat=True)) != ["Camper"]:
            raise ValueError("Unexpected account role")
        before = User.objects.filter(pk=user.pk).values().get()
        call_command("authorize_account", user.email, role="Camper", attest_identity_checked=True)
        expected = {**before, "approved": True, "security_version": before["security_version"] + 1}
        if User.objects.filter(pk=user.pk).values().get() != expected:
            raise ValueError("Account preservation check failed")
        if SocialAccount.objects.get(pk=link.pk).user_id != user.pk:
            raise ValueError("Link preservation check failed")
    print(
        "Only the existing Google-linked Camper account was approved; other account fields and policies preserved."
    )
except Exception:
    raise SystemExit(
        "Approval failed; transaction rolled back and sensitive diagnostics withheld."
    ) from None
```

## Owner authorization

The owner explicitly confirmed: “Yes—this is my account; approve Camper access” on
2026-11-26. This authorizes only the concrete sole-account approval above. It is not approval
to disable registration approval, grant staff/admin access, alter MFA, verify another email
or auto-link accounts. The protected command's identity attestation follows this confirmation;
no attestation was made before it. Eight existing Google eligibility/approved-login/MFA/
registration tests and three synthetic approval-wrapper tests passed before live approval.

## Executed result

The exact approved command completed successfully. The existing protected operator workflow
recorded authorization; the sole Google-linked account is approved as Camper, its security
version incremented, and in-transaction comparisons verified that all other account fields
and its Google link were preserved. No administrator/staff access, policy change, email
attestation, MFA bypass, credential rotation, migration, new image or deployment occurred.

This removes a verified authorization blocker. The supplied HAR alone did not prove every
callback stage succeeded; the synthetic invalid-code probe did not authenticate a real user.
The owner must start a fresh browser sign-in to confirm live end-to-end success. The generic
403 presentation for pending accounts remains a usability limitation; a future improvement
must not disclose account existence or approval status before identity verification.

Validation: eight existing Google policy/login/MFA tests and three synthetic command tests
passed. The command's live preservation checks passed. No new runtime dependency or migration;
no production-readiness claim. Google client/redirect/scope settings did not need alteration.
Reference for interpreting token error categories:
[Google OAuth web-server documentation](https://developers.google.com/identity/protocols/oauth2/web-server).

Repeat local checks with the protected synthetic PostgreSQL running:

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh tests/security/test_google_oauth.py -k 'ineligible_accounts or existing_google_login or google_login_still_requires_enrolled_mfa or google_registration_preserves_policy' -q --assert=plain --tb=no --show-capture=no
TEST_DATABASE_PORT=55433 sh scripts/test.sh .runtime/google-login-diagnosis-20261126/test_approval.py -q --assert=plain --tb=no --show-capture=no
```

The private wrapper harness uses synthetic accounts and the repository fixtures; it does not
contain HAR data. Do not rerun the completed one-time approval: it refuses an already approved
account. No HAR code, state, cookie, personal identifier or raw response is included here.
