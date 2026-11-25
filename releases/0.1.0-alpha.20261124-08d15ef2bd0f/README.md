# Published prerelease

Tag: `0.1.0-alpha.20261124-08d15ef2bd0f`. Date: 2026-11-24.

**Evaluation only; not production-ready.** Both linux/amd64 and linux/arm64 were built,
scanned and executed; anonymous registry pulls and exact index digests were verified.

| Component | Published image index |
|---|---|
| web | `docker.io/thecyberbutler/campground-web@sha256:245643130c461d07dadb9a3d529f7379711e740838921f28cd9564b27227c145` |
| db | `docker.io/thecyberbutler/campground-db@sha256:529eda56356369e6a225d8870c73683d6e0fac433b13c5b0bf7a82e51c29ed8d` |
| proxy | `docker.io/thecyberbutler/campground-proxy@sha256:4652c527f6235d929eb5f1fd41c08f171f416e76d53620a9f7ba3200a4bbe835` |

Source snapshot SHA-256: `08d15ef2bd0f7bcc8268647335b2e82b2bd59a5d3e03fee58f4616656b7f8cfe`.

The snapshot includes reviewed uncommitted application work; this is not a clean Git tag.
153 PostgreSQL tests and the 85% coverage gate passed on the release snapshot before
publication. Per-platform vulnerability and secret scans passed. See the implementation
progress record for additional repository regression tests and remaining security gates.

Use `images.env` with `compose.yaml` and `compose.registry.yaml` as described in
`docs/container-publishing.md`. All images use UID/GID 10001; preserve protected secret
ownership/modes. No secrets, camper database, user accounts or TLS volumes are included.

Public distribution was explicitly approved by the owner in SD-025. Image publication is
not approval to deploy to production or open campground booking.
