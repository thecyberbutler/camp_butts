# Test Administrator promotion — 2026-11-26

The owner explicitly requested Administrator access for their existing Georgia Mountain
Fairgrounds test account. This uses the existing audited, tenant-scoped operator workflow,
not a Django superuser. The owner previously identified the sole Google-linked account as
theirs. Ambiguous selection, unexpected role/email/environment or permission state fails
closed. The exact script and command below are disclosed before SSH. No passwords, provider
tokens, MFA material or personal identifiers are printed.

## Exact command

```sh
ssh -T -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no -o ClearAllForwardings=yes -o ControlMaster=no -o ControlPath=none -o ConnectTimeout=10 camp-butts-test 'sudo -n docker compose -p camp-butts-test --project-directory /opt/camp-butts-test --env-file /opt/camp-butts-test/.env --env-file /opt/camp-butts-test/images.env -f /opt/camp-butts-test/compose.yaml -f /opt/camp-butts-test/compose.registry.yaml -f /opt/camp-butts-test/compose.google.yaml exec -T web python -' < /Users/michaelbutler/Repos/camp_butts/.runtime/admin-promotion-20261126/promote.py
```

## Exact Python stdin

```python
"""Owner-authorized, test-only promotion of the sole Google-linked Camper."""

try:
    import django

    django.setup()
    from allauth.account.models import EmailAddress
    from allauth.mfa.models import Authenticator
    from allauth.socialaccount.models import SocialAccount
    from django.conf import settings
    from django.core.management import call_command

    from apps.accounts.models import User
    from apps.configuration.models import Campground
    from apps.tenancy.context import lookup, tenant_scope

    if settings.APP_ENVIRONMENT not in {"development", "test"} or settings.DEBUG:
        raise ValueError("Requires hardened test environment")
    expected_permissions = {
        "reservations.operate_reservations",
        "reservations.block_campsite",
        "reservations.view_occupancy",
        "accounts.approve_camper",
        "accounts.manage_camper",
        "campsites.add_campsite",
        "campsites.change_campsite",
        "campsites.add_campsitetype",
        "campsites.add_amenity",
        "configuration.change_campground",
        "audit.view_event",
    }
    with tenant_scope(lookup("georgia-mountain-fairgrounds")):
        Campground.current(lock=True)
        links = SocialAccount.objects.filter(provider="google")
        if links.count() != 1:
            raise ValueError("Ambiguous account selection")
        link = links.only("id", "user_id").get()
        user = User.objects.select_for_update().defer("password").get(pk=link.user_id)
        if (
            not user.is_active
            or not user.approved
            or user.is_staff
            or user.is_superuser
            or user.get_all_permissions()
            or set(user.groups.values_list("name", flat=True)) != {"Camper"}
        ):
            raise ValueError("Unexpected account state")
        verified = (
            EmailAddress.objects.filter(
                user=user, email=user.email, primary=True, verified=True
            ).exists()
            and not EmailAddress.objects.filter(user=user, verified=False).exists()
        )
        if not verified:
            raise ValueError("Existing email verification required for MFA")
        before_version = user.security_version
        call_command(
            "authorize_account", user.email, role="Administrator", attest_identity_checked=True
        )
        updated = User.objects.defer("password").get(pk=user.pk)
        if (
            not updated.is_active
            or not updated.approved
            or not updated.is_staff
            or updated.is_superuser
            or updated.security_version != before_version + 1
            or updated.get_all_permissions() != expected_permissions
            or set(updated.groups.values_list("name", flat=True)) != {"Administrator"}
            or not links.filter(pk=link.pk, user_id=user.pk).exists()
        ):
            raise ValueError("Promotion verification failed")
        enrolled = Authenticator.objects.filter(user=updated, type="totp").exists()
        has_local_password = updated.has_usable_password()
    print("Administrator promotion committed for Georgia Mountain Fairgrounds only.")
    print("No superuser access. Existing sessions revoked. Verified email retained.")
    print("TOTP already enrolled:", enrolled)
    print("Usable local password:", has_local_password)
except Exception:
    raise SystemExit(
        "Promotion failed; transaction rolled back; sensitive diagnostics withheld."
    ) from None
```

## Status

Executed successfully after disclosure. The fixed output confirmed campground-only
Administrator promotion, no superuser access, session revocation and existing verified
email. TOTP enrolled: false. Usable local password: false. No image/config/schema change
or service restart was needed. Do not rerun this one-time script.

Validation: five synthetic PostgreSQL wrapper tests passed (promotion/audit/session version,
ambiguous Google links, production refusal, audit rollback and unverified email refusal).
Nine existing role/authentication/MFA tests also passed, including Google sign-in requiring
enrolled MFA and single-use recovery-code behavior. Gitleaks passed for the private scripts.
Human password establishment, MFA enrollment and privileged browser acceptance remain pending.

Repeat local validation with the existing isolated synthetic database running:

```sh
TEST_DATABASE_PORT=55433 sh scripts/test.sh .runtime/admin-promotion-20261126/test_promote.py tests/integration/test_workflows.py::test_role_setup_and_protected_operator_authorization tests/security/test_accounts.py tests/security/test_google_oauth.py::test_google_login_still_requires_enrolled_mfa -q --assert=plain --tb=no --show-capture=no
```

Private scripts/tests are intentionally ignored under `.runtime/admin-promotion-20261126/`.
The complete operation is retained above; normal tracked authentication regressions remain
in tests/security/test_accounts.py and tests/security/test_google_oauth.py.
