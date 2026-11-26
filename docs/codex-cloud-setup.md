# Codex Cloud setup: blocked Alpine repository

## Observed status — 2026-11-26

The owner's setup report says locked Python dependencies and the proxy build completed;
lint, formatting, Bandit, dependency audit, Compose configuration and Django checks passed.
Those are reported Cloud results, not independently rerun in this local desktop task.
PostgreSQL build was blocked by denied access to `dl-cdn.alpinelinux.org`, so Cloud database
tests and application startup remain unverified. The saved `camp_butts` configuration is
listed as ready/runnable; that status does not establish application or database readiness.

`Dockerfile.db` deliberately upgrades libxml2 from the Alpine package repository before
creating the non-root runtime user. Do not remove that security update or replace the
image with an unreviewed version to bypass the denial. This chat has no attached Cloud
executor, network-editing tool or access to the setup chat's saved installation instructions.

## Proposed narrow remediation

Owner approval is pending for adding only `dl-cdn.alpinelinux.org` to the Cloud development
environment's existing restricted host allowlist. Keep all existing entries and restrictions;
do not replace the list, enable unrestricted Internet access, add wildcard domains, change
the application's Google egress allowlist, or copy AWS credentials/data into Cloud.

This expands development egress and exposes the build to upstream package supply-chain
risk. Keep verified HTTPS, official APK signatures and digest-pinned base images. Retaining
the denial preserves the boundary but leaves builds incomplete. Existing reviewed,
compatible digest-locked images can be evaluated separately; do not assume they satisfy
this environment's architecture and synthetic test-user ownership requirements.

After specific approval, review the saved single-host addition in the **setup environment's
settings**, then save it using the offered Save/Save draft action. The local desktop cannot
apply this for the owner. Remove the addition to roll back; future uncached builds may need
it again. Existing downloads cannot be recalled by removing network access.

Resume the original setup chat with:

> Recheck that the saved restricted network policy permits only the approved additional
> host dl-cdn.alpinelinux.org. Retry the blocked PostgreSQL build using the existing locked
> Dockerfile and original setup commands. Preserve proxy routing, TLS/APK verification,
> non-root containers and protected synthetic credentials. Run the PostgreSQL security and
> concurrency suite, then validate application startup and deployment checks. Report actual
> results and any remaining failures. Do not publish the environment until validation succeeds.

Use the actual build step as the decisive connectivity test; a successful host curl alone
does not verify nested Docker build networking. If a new TLS failure appears, use the
Cloud runtime skill's BuildKit secret CA-mount procedure for the individual build step;
never disable verification or bake session CA/credentials into image layers. Do not change
the tracked Dockerfile merely to remove a network-policy denial.

## Validation after access is saved

Reuse that setup's existing container name, UID/GID, protected files and database port.
The repository's supported synthetic database setup is in README.md, and validation is:

```sh
# Set TEST_DATABASE_PORT to the existing isolated Cloud database's loopback port.
.venv/bin/python scripts/provision_test_db.py
sh scripts/test.sh -q --assert=plain --tb=no --show-capture=no --cov --cov-fail-under=85
docker compose config --quiet
# After following docs/deployment.md with isolated development credentials:
docker compose exec -T web python manage.py check --deploy --fail-level WARNING
```

Both Python commands use TEST_DATABASE_PORT from the environment (default 55432); preserve
the setup's configured value. Provision only the synthetic test database, never the AWS
database. Preserve existing volumes; do not recreate containers blindly. Include the
existing container-boundary/image checks and actual HTTPS startup checks from the setup
instructions. Publish only after the remaining validation passes, then verify a fresh task
started from that published environment. No network setting or Cloud validation has been
changed or independently completed in this desktop task.
