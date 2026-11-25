# Dependency inventory

Reviewed 2026-11-24. Exact artifacts and hashes are in `poetry.lock`; Python source is
PyPI over verified HTTPS. No extra package indexes are configured. The installed platform dependency set was checked with pip-audit, which reported no known
findings. Lock entries excluded by platform markers still require review on their target
platform.
That result is time-bound and does not cover OS packages or guarantee safety.

## Purpose and review

The mandatory stack uses Django (framework/auth/templates), allauth (registration,
recovery/MFA), Axes (authentication throttling), Psycopg (PostgreSQL) and Argon2-cffi
(password hashing). Cryptography supplies established Fernet encryption for MFA/session
storage; Gunicorn serves the application. These maintained upstream projects are locked
to the reviewed supported releases below. The owner-approved proxy migration adds WhiteNoise 6.12.0 for collected static assets;
it has no required transitive dependencies and uses the MIT license. Autorefresh, source
finders, wildcard CORS and additional static roots are disabled. Its patched file-access
behavior and Django/Python support were reviewed in the upstream changelog.

Development-only pytest/pytest-django/pytest-cov support PostgreSQL/security tests; Ruff,
Bandit and pip-audit provide lint and security checks. They are omitted from the runtime
image. Poetry 2.5.2 is used only in the build stage. Its bootstrap transitive resolution
is not part of the application lock: a separately hash-locked builder/toolchain and
builder scanning remain supply-chain release work. Do not treat runtime scans as builder
validation. The application runtime removes unused package installers.

License identifiers below come from installed package metadata. Retain upstream license notices and review copyleft/distribution obligations (including
Psycopg LGPL-3.0, PostgreSQL,
libpq and OS packages) before release. No project license is asserted by this inventory.
Full legal/distribution review is not claimed.

## Locked Python dependencies, including transitives

| Package | Version | Group | Metadata license |
|---|---|---|---|
| argon2-cffi | 25.1.0 | main | MIT |
| argon2-cffi-bindings | 26.2.0 | main | MIT |
| asgiref | 3.13.0 | main | BSD-3-Clause |
| bandit | 1.9.4 | dev | Apache-2.0 |
| boolean-py | 5.0 | dev | BSD-2-Clause |
| cachecontrol | 0.15.0 | dev | Apache-2.0 |
| certifi | 2026.11.20 | dev | Mozilla Public License 2.0 (MPL 2.0) |
| cffi | 2.1.1 | main | MIT-0 |
| charset-normalizer | 3.5.3 | dev | MIT |
| colorama | 0.4.6 | main, dev | Review upstream license |
| coverage | 7.17.5 | dev | Apache-2.0 |
| cryptography | 50.0.2 | main | Apache-2.0 OR BSD-3-Clause |
| cyclonedx-python-lib | 11.12.0 | dev | Apache Software License |
| defusedxml | 0.7.1 | dev | Python Software Foundation License |
| django | 5.2.19 | main | BSD-3-Clause |
| django-allauth | 65.22.1 | main | MIT |
| django-axes | 9.1.0 | main | MIT |
| fido2 | 2.2.1 | main | BSD License; Apache Software License; Mozilla Public License 2.0 (MPL 2.0) |
| filelock | 4.3.1 | dev | MIT |
| gunicorn | 27.0.1 | main | MIT |
| idna | 3.20 | dev | BSD-3-Clause |
| iniconfig | 2.3.1 | dev | MIT |
| license-expression | 30.4.4 | dev | Apache-2.0 |
| markdown-it-py | 4.3.0 | dev | MIT License |
| mdurl | 0.1.2 | dev | MIT License |
| msgpack | 1.2.4 | dev | Apache-2.0 |
| packageurl-python | 0.17.6 | dev | MIT License |
| packaging | 26.4 | dev | Apache-2.0 OR BSD-2-Clause |
| pip | 26.3 | dev | MIT |
| pip-api | 0.0.35 | dev | Apache Software License |
| pip-audit | 2.10.1 | dev | Apache Software License |
| pip-requirements-parser | 32.0.1 | dev | MIT |
| platformdirs | 4.14.8 | dev | MIT |
| pluggy | 1.7.0 | dev | MIT License |
| psycopg | 3.3.9 | main | LGPL-3.0-only |
| psycopg-binary | 3.3.9 | main | LGPL-3.0-only |
| py-serializable | 2.2.0 | dev | Apache Software License |
| pycparser | 3.12 | main | BSD-3-Clause |
| pygments | 2.21.0 | dev | BSD-2-Clause |
| pyparsing | 3.3.3 | dev | MIT |
| pytest | 9.2.0 | dev | MIT |
| pytest-cov | 7.1.0 | dev | MIT |
| pytest-django | 4.14.0 | dev | BSD License |
| pyyaml | 6.0.4 | dev | MIT License |
| qrcode | 8.2 | main | BSD License; Other/Proprietary License |
| requests | 2.34.2 | dev | Apache Software License |
| rich | 15.0.0 | dev | MIT License |
| ruff | 0.17.6 | dev | MIT |
| sortedcontainers | 2.4.0 | dev | Apache Software License |
| sqlparse | 0.6.1 | main | BSD License |
| stevedore | 5.10.0 | dev | Apache-2.0 |
| tomli | 2.5.0 | dev | MIT |
| tomli-w | 1.2.0 | dev | MIT License |
| tzdata | 2026.6 | main | Review upstream license |
| urllib3 | 2.8.0 | dev | MIT |
| whitenoise | 6.12.0 | main | MIT |

## Locally served frontend

Bootstrap 5.3.8 CSS (MIT) and HTMX 2.0.11 (0BSD) come from the official npm registry.
`static/vendor/inventory.json` records source archives, registry SHA-512 SRI and SHA-256
file hashes; upstream license files are retained. Only Bootstrap CSS is included, so
Bootstrap JavaScript/Popper are not application runtime dependencies. HTMX evaluation,
response scripts and history caching are disabled. No CDN or tracking requests are used.
The vendoring process verifies integrity; broader frontend advisory/manual review remains
a release task and is not represented by pip-audit.

## Container and scanner inventory

| Component | Version/base | Pinned source digest |
|---|---|---|
| Web/build | Python 3.13.18 / Alpine 3.24.4 | `python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e` |
| Database | PostgreSQL 17.12 / Alpine; libxml2 patched at build | `postgres:17.12-alpine@sha256:f9cf3e1f0066f0eb0c48707d864f0ac5941e9ff454a072077d97a4d278d07d73` |
| Proxy | Traefik 3.7.20 / Alpine | `traefik:v3.7.20@sha256:8301d6f60957a422f98918aacf2b01482abde3e74ead3719aabdb7c64045fe28` |
| Secret scanner | Gitleaks | `ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f` |
| Image/source scanner | Trivy 0.76 | `aquasec/trivy@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb` |

Final web/Traefik image scans and the unchanged hardened database scan reported zero
high/critical findings. Caddy has been removed from the deployment; its original findings
remain in `security-findings.md` with a removal disposition. No finding was suppressed. New deployments
remain blocked until all release gates pass. Restic is planned for encrypted backups;
a supported exact version, integrity check and restore drill are still required.

## Update procedure

Review upstream maintenance, release notes, licenses and advisories before changing a
constraint. Resolve using Poetry, inspect all transitive lock changes, retain hash checks,
run pip-audit/Bandit/Gitleaks and the real PostgreSQL suite. Re-vendor frontend archives
only after reviewing versions and integrity. Rebuild all images against reviewed pinned
bases, record output digests, scan OS and language packages, and validate migrations,
non-root execution, role isolation and HTTPS. Never suppress findings to make a gate pass.
Keep old DB volumes for controlled recovery; base-OS changes require logical restore into
fresh volumes. Schedule routine review and urgent fixes for applicable advisories.

## Proxy migration review sources

Traefik's maintained 3.7 patch release was selected over older unsupported series and
pinned by image digest after scanning. Traefik is MIT-licensed; distribution must retain
its upstream and bundled-component notices. No plugins or discovery dependencies are
configured. The complete container, including bundled Go modules/OS packages, was scanned.
WhiteNoise was added as an exact Poetry pin with artifact hashes; the lock diff contains
only WhiteNoise and the lock content hash. Its optional Brotli dependency was not enabled.

- [Traefik 3.7.20 release](https://github.com/traefik/traefik/releases/tag/v3.7.20)
- [Traefik security release announcement](https://community.traefik.io/t/new-security-update-for-traefik-2-11-2-11-64-3-7-3-7-20-and-3-8-3-8-0/30561)
- [File provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/others/file/)
- [Forwarded headers](https://doc.traefik.io/traefik/reference/install-configuration/entrypoints/)
- [WhiteNoise changelog](https://whitenoise.readthedocs.io/en/stable/changelog.html)
- [WhiteNoise package metadata](https://pypi.org/project/whitenoise/6.12.0/)


## SaaS integration review

No Python/frontend dependency or image-base change is required for tenancy. Uses existing
Django transactions, Psycopg parameter binding/composable SQL, PostgreSQL schemas/RLS, and
allauth's settings/token-generator hooks. Django's private ContentType manager cache mapping
is deliberately disabled; pytest-django's transaction fixture is wrapped only in tests.
Reassess these integration points on dependency upgrades. No custom crypto primitive,
managed tenant library/service or additional infrastructure was introduced.
