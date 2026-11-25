# Google sign-in prerelease

Version `0.1.0-alpha.20261125-3386d5caf5b3`, source SHA-256
`3386d5caf5b35e116a396b148e32ab07642cadfa7dd94f6fa64b6eba1ff78b87`.
AMD64 and ARM64 images were built, scanned and published to the existing owner-approved
public Docker Hub repositories. `images.env` records independently verified registry
manifest digests. Google egress uses a separate tag in `campground-proxy`.

Validation: 235 PostgreSQL tests passed with coverage above 85%; Ruff/format/Bandit,
source Gitleaks, Trivy dependency/Dockerfile and per-architecture HIGH/CRITICAL + secret
scans passed. Both architectures ran as non-root; missing-secret startup failed closed.
Real proxy checks verified Google TLS, denied private/metadata/mapped-metadata targets,
wrong peer/port/method and direct Internet isolation. Publication repeated these gates.
Database/Traefik AMD64 filesystem layers match the previous deployment exactly.

This is a development prerelease, not production-ready. Live human Google consent and
approved-user sign-in, complete encrypted recovery, host review, renewal and remaining
production security gates are not implied by these results. See implementation progress
and the Google deployment transcript for actual deployment status.
