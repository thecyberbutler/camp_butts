# Interface modernization prerelease

Version `0.1.0-alpha.20261125-5815b9993895`, source SHA-256
`5815b99938950eb13960fd456a2c809f3725f6b61d39bc4230c490875ad08a60`.
Application changes are from Git commit `f562aba` and its preceding repository maintenance
commits. The digest identifies the allowlisted build snapshot, not the Git tree hash.

AMD64 and ARM64 web/database/Traefik/Google-egress images were built, scanned and published
to the previously approved public `thecyberbutler` Docker Hub repositories. Both build and
publication passed 235 PostgreSQL tests with the 85% coverage gate, Ruff lint/format, Bandit,
Gitleaks source scanning, Trivy source/dependency/configuration and per-architecture image
HIGH/CRITICAL vulnerability and secret scans. Both architectures passed non-root execution
and missing-secret startup checks; the disposable Google proxy boundary checks passed twice.
Poetry lock validation passed with existing metadata deprecation warnings; pip-audit reported
no known vulnerabilities. Every remote registry manifest digest was independently verified.

Compared with `0.1.0-alpha.20261125-3386d5caf5b3`, the DB, Traefik and Google egress filesystem
layers are identical on both architectures. All image runtime configurations are unchanged
apart from release labels; only the web presentation content changed. No new dependencies,
migrations, database grants, network, secret or authentication-control changes are introduced.

Use `images.env` with the existing base/registry/Google Compose files. The exact AWS upgrade,
backup/rollback and validation transcript is in `docs/aws-ui-deployment-transcript.md`.
Deployment results are recorded there and in `docs/implementation-progress.md`.

This is a development prerelease, not production approval. Human Google consent/sign-in,
complete encrypted/off-host recovery, host review, certificate-renewal monitoring, additional
browser/accessibility review and other production release gates remain outstanding. Scanning
does not prove absence of vulnerabilities; no finding was suppressed for this release.
