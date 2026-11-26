# Docker Hub images and deployment

Status: prerelease evaluation only. The platform is not approved for production. Docker Hub
stores distributable images; application operation/data remain self-hosted. Publishing an
image does not satisfy outstanding backup/restore, SMTP, ACME, load, manual review or other
release gates. The owner explicitly approved public source visibility in SD-025.

Repositories:

- https://hub.docker.com/r/thecyberbutler/campground-web
- https://hub.docker.com/r/thecyberbutler/campground-db
- https://hub.docker.com/r/thecyberbutler/campground-proxy

Each image supports **linux/amd64 and linux/arm64**, runs as **10001:10001**, and retains the
existing hardened Dockerfiles. The web image also supplies controlled provisioning and
migration jobs. There is no `latest`/stable alias. Tags include a prerelease version and
12 characters of the allowlisted source snapshot's SHA-256. Uncommitted reviewed work is
included in that snapshot; a tag is not falsely represented as a clean Git commit.

## Deploy from images

Use the published `releases/<tag>/images.env` together with `compose.yaml` and
`compose.registry.yaml`. The overlay removes every local build instruction and retains
all network, filesystem, capability, resource, health, secret and migration boundaries.
It reuses the same web digest for web/migrate/provision. Images are referenced by manifest
digest, so changes to registry tags cannot silently replace the deployed contents.

Follow `deployment.md` for host hardening and fresh protected secrets. The dedicated host
identity/secret owner must be UID/GID **10001**, matching these images. Leave APP_UID and
APP_GID at 10001. Do not compensate for ownership mismatches with root, chmod 644 secrets,
extra capabilities or a runtime chown. Existing deployments with different UID/GID or
base-OS data need a separately validated migration; preserve old volumes and encrypted
backups. Local source builds remain supported for their existing development identities.

Set non-secret `.env` values for APP_DOMAIN, DJANGO_ALLOWED_HOSTS and SECRETS_DIR. Replace
`releases/<tag>/images.env` below with the actual checked-in release file:

```sh
docker compose --env-file .env --env-file releases/<tag>/images.env -f compose.yaml -f compose.registry.yaml config --quiet
docker compose --env-file .env --env-file releases/<tag>/images.env -f compose.yaml -f compose.registry.yaml --profile tools pull
```

Use that same pair of `--env-file` and `-f` arguments for **every** provisioning, migration,
collectstatic, startup, health and backup-related command in the deployment guide. Fresh
install order remains DB → register campground → tenant migrations → setup_roles → optional
initial import → protect/grant/activate → collectstatic → web/proxy. There are no default
credentials and no automatic startup migration. Georgia Mountain Fairgrounds' reference
profile is bundled for optional explicit import, but its accounts/data are not in the image.

After initialization, start with `up -d --no-build`; only the reverse proxy publishes ports.
Image pulls do not perform migrations or upgrade database volumes. For upgrades, take a
verified encrypted backup, stop routing/jobs, migrate each tenant once, reapply grants,
collect assets, then restart and validate. Roll back to a reviewed digest only with a
compatible schema; never remove occupancy/RLS constraints or restore stale sessions.

## Build and publish another prerelease

Requirements: trusted Docker Engine/Desktop with containerd image store, Buildx support for
both platforms, Poetry development environment and the protected synthetic PostgreSQL test
service on loopback (default 55433). No Docker socket is mounted in scanner/app containers.

```sh
.venv/bin/python scripts/release_images.py build --namespace thecyberbutler --version 0.1.0-alpha.20261124
```

The command prints the private candidate directory under ignored `.runtime/releases`.
It creates a fixed allowlisted snapshot without `.git`, `.env`, `.secrets`, local editor configuration, database
volumes or mutation artifacts. Source files have ordinary read modes **inside a 0700 parent
workspace**, preserving non-root image readability without making the host workspace public.
It executes Ruff, Bandit and the real PostgreSQL suite/85% coverage gate, Gitleaks source
scanning, Trivy source/lock (including dev dependencies)/Dockerfile checks, and separate
vulnerability and secret scans for **each image architecture**. High/critical vulnerabilities
and all detected image secrets block publication. Non-root execution and missing-secret
startup checks run for both architectures. Raw child output is withheld to protect secrets.
A failure is not a pass; reproduce only the specific safe check without printing credentials.

Log in locally using Docker's protected credential store:

```sh
docker login --username thecyberbutler
```

Enter a scoped Docker Hub access token in the local prompt; never put it in chat, command-line
arguments, source or `.env`. The publisher retrieves it only in memory through Docker's
credential helper, uses verified HTTPS without redirects and never prints/persists it.
Read/write permissions are sufficient for pushing; repository administration may require
an owner UI action. Do not broaden token permissions just to avoid that action.

After review, publish the manifest from the completed build:

```sh
.venv/bin/python scripts/release_images.py publish .runtime/releases/candidate-EXAMPLE/manifest.json --public-approved
```

`--public-approved` records the operator's use of an explicit visibility approval; it is
not a security bypass. Without it, the publisher requires private repositories. It never
silently changes an existing repository's visibility. Namespace/component/tag/digest/source
validation rejects redirected or incomplete manifests. The publisher reruns current checks,
scans both architectures again, verifies the local digests have not changed, refuses a
conflicting existing tag, pushes the reviewed indexes and verifies remote digests before
writing `images.env`. No rebuild occurs during push. Keep the resulting digest lock in a
trusted release record. A partially failed push does not produce a complete deployment lock;
retry only the same reviewed digest, never overwrite a different existing tag.

Minimal BuildKit provenance is retained; it is not an independent signature or proof of
publisher trust. Digest locks protect content identity, but their trusted delivery and the
publisher account/host remain security boundaries. Enable MFA on the Docker Hub account,
limit token scope, and review advisories before every rebuild. The current builder's Poetry
bootstrap still has the previously documented unpinned transitive toolchain limitation;
full production toolchain/release assurance remains outstanding.

## Official references

- [Docker Hub repository visibility](https://docs.docker.com/docker-hub/repos/manage/access/)
- [Docker credential stores and login](https://docs.docker.com/reference/cli/docker/login/)
- [Compose merge/reset behavior](https://docs.docker.com/reference/compose-file/merge/)
- [Build provenance](https://docs.docker.com/build/metadata/attestations/slsa-provenance/)
- [Immutable tags](https://docs.docker.com/docker-hub/repos/manage/hub-images/immutable-tags/)

Public distribution exposes application source/dependency metadata by approved design.
It does not grant a project software license or authorize publication of secrets/data.
Retain bundled upstream notices; complete the existing distribution/license review before
production release. Registry availability/rate limits affect fresh pulls; already running
self-hosted containers do not need Docker Hub to handle reservations.

## Optional Google egress image

Google-enabled releases build a fourth component, using the existing approved public
`thecyberbutler/campground-proxy` repository with tag `google-egress-<release-tag>`.
The release lock adds `CAMPGROUND_EGRESS_IMAGE`; no fourth repository or broader registry
permissions are required. Deploy with `compose.google.yaml` only when its restricted-egress
approval and protected client configuration exist. Historical three-component digest locks
remain usable for their original deployments; the current publisher requires all four
components for new releases.

Both egress architectures undergo vulnerability/secret scans and non-root config parsing.
A real disposable Docker network test verifies permitted Google TLS, unapproved destinations,
private/metadata addresses including mapped IPv6, wrong peers/ports/methods and lack of direct
Internet access. Publication repeats all gates and refuses mutable tag collisions. Runtime
Google credentials are never part of the source snapshot, build context or image.

## Latest evaluated interface release

`0.1.0-alpha.20261125-5815b9993895` is published for AMD64/ARM64 and deployed on the authorized
AWS test instance. The committed release manifest and digest lock are under its `releases/`
directory. Both build and publication repeated the source/image/test/egress gates; public
acceptance and runtime boundary checks passed. This is still a prerelease with the existing
production gates. See `aws-ui-deployment-transcript.md`; no stable or latest tag was created.
