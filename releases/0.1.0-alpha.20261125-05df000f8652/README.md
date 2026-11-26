# Email-only identity and Google profile prerelease

Version `0.1.0-alpha.20261125-05df000f8652`, source SHA-256
`05df000f8652494fc81bff1cdebf076cd9692e47fc8d849936899e0d135acf66`.
Application features are commits `47bc241` and `1c2cbbf`. This hash identifies the allowlisted
build snapshot, not the Git tree. AMD64/ARM64 web, PostgreSQL, Traefik and Google egress images
are published in the previously approved public `thecyberbutler` repositories. Remote manifest
digests were verified; use `images.env` with the base/registry/Google Compose files.

Both build and publication passed 271 PostgreSQL tests and the 85% coverage gate, Ruff lint/
format, Bandit, Gitleaks, Trivy source/configuration/dependency and per-architecture image
HIGH/CRITICAL and secret gates. Non-root startup and real restricted Google/People egress
checks passed. pip-audit found no known vulnerabilities; Poetry lock checks passed with
existing metadata deprecation warnings. DB/proxy filesystem layers and all runtime image
configurations match the prior interface release on both architectures except release labels.
The web code and explicitly approved People API proxy allowlist change. No new dependency.

Upgrade requires `accounts.0003_email_identity`: stop writers, encrypt/verify a database
snapshot, validate emails, migrate under the tenant migrator, reapply reviewed grants and
validate security boundaries. Sessions are retired and legacy lockouts carried forward.
Never restart a username-based image on the new schema. The exact command/script transcript
and actual deployment status are in `docs/aws-email-profile-deployment-transcript.md`.

This is a test prerelease. Human Google consent/profile/sign-in, full isolated/off-host
recovery, host review, lower-severity review and other production gates remain outstanding.
No security finding was suppressed and no new security exception was introduced.
