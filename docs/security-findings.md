# Image security findings

Reviewed 2026-11-24. Proxy migration complete; overall production release remains blocked
by unfinished release gates. No security exceptions or suppressions approved.

These are scanner findings, not independent exploit verification. Counts are package/advisory pairs; a shared library may appear in multiple installed packages. Application Poetry dependency auditing passed, but that does not cover base-image OS packages or bundled build tools.

## Remediation and current status

Fresh scans of the hardened application and database images reported **zero HIGH/CRITICAL**
findings. The initial 52 web and 145 database package/advisory pairs below are historical,
resolved in the replacement images by patched Alpine bases, removal of unused runtime pip
and gosu, and a libxml2 update. This is scanner evidence, not proof of absence of vulnerabilities.
The full PostgreSQL test suite passed on the replacement database; fresh-volume deployment
validation is recorded in implementation progress. Existing volumes were preserved.

Caddy's two HIGH findings are **removed from the current deployment by replacing Caddy**
with scanned Traefik 3.7.20. The old Caddy image remains affected; these are not claims of
upstream fixes:

- CVE-2026-116587: bundled go-jose/v3 3.0.5; upstream reports RSA JWK parameter CPU denial
  of service. A v4 fix is not a compatible v3 drop-in replacement.
  [Upstream advisory](https://github.com/go-jose/go-jose/security/advisories/GHSA-mgcc-cww5-fp2q).
- CVE-2026-78661: golang.org/x/net 0.60.0; reported HTML-parser quadratic work, fixed in
  0.62.0. [Upstream issue](https://go.dev/issue/82224).

Applicability through the former Caddy configuration was not established. No finding was
suppressed or exception granted. The owner explicitly requested Traefik; final Traefik
and WhiteNoise-enabled web images each passed the HIGH/CRITICAL gate. Verified HTTPS and
security-boundary tests passed. Do not reactivate the old Caddy image without a separate
security review. Lower-severity findings still require release review.

The stale staff-request gap and potential old-session revival after account reactivation
were addressed with locked authorization checks and security-version increments. Regression
tests cover committed revocation between request initialization and the mutation.

## Initial web image — 52 high/critical findings (resolved in replacement)

| Package | Advisory | Severity | Installed | Reported fix |
|---|---|---|---|---|
| bsdutils | CVE-2026-53613 | HIGH | 1:2.38.1-5+deb12u3 | Not reported |
| bsdutils | CVE-2026-53615 | HIGH | 1:2.38.1-5+deb12u3 | Not reported |
| bsdutils | CVE-2026-78410 | HIGH | 1:2.38.1-5+deb12u3 | Not reported |
| gzip | CVE-2026-41992 | HIGH | 1.12-1 | Not reported |
| libacl1 | CVE-2026-54369 | HIGH | 2.3.1-3 | Not reported |
| libblkid1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libblkid1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libblkid1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libmount1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libmount1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libmount1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libncursesw6 | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| libpam-modules | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libpam-modules-bin | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libpam-runtime | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libpam0g | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libsmartcols1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libsmartcols1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libsmartcols1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libsqlite3-0 | CVE-2025-7458 | CRITICAL | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-11822 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-11824 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-119373 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-119374 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-119379 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libssl3 | CVE-2026-107494 | HIGH | 3.0.22-1~deb12u2 | Not reported |
| libsystemd0 | CVE-2026-16742 | HIGH | 252.39-1~deb12u2 | Not reported |
| libtinfo6 | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| libudev1 | CVE-2026-16742 | HIGH | 252.39-1~deb12u2 | Not reported |
| libuuid1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libuuid1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libuuid1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| mount | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| mount | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| mount | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| ncurses-base | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| ncurses-bin | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| openssl | CVE-2026-107494 | HIGH | 3.0.22-1~deb12u2 | Not reported |
| perl-base | CVE-2026-9538 | HIGH | 5.36.0-7+deb12u4 | Not reported |
| util-linux | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux-extra | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux-extra | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux-extra | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| zlib1g | CVE-2023-45853 | CRITICAL | 1:1.2.13.dfsg-1 | Not reported |
| zlib1g | CVE-2026-85091 | HIGH | 1:1.2.13.dfsg-1 | Not reported |
| msgpack | CVE-2026-114613 | HIGH | 1.1.2 | 1.2.3 |
| msgpack | GHSA-6v7p-g79w-8964 | HIGH | 1.1.2 | 1.2.1 |
| setuptools | CVE-2025-47273 | HIGH | 70.3.0 | 78.1.1 |
| urllib3 | CVE-2026-97687 | HIGH | 2.7.0 | 2.8.0 |
| urllib3 | CVE-2026-97689 | HIGH | 2.7.0 | 2.8.0 |

## Historical Caddy image — 2 high/critical findings (component removed)

| Package | Advisory | Severity | Installed | Reported fix |
|---|---|---|---|---|
| github.com/go-jose/go-jose/v3 | CVE-2026-116587 | HIGH | v3.0.5 | Not reported |
| golang.org/x/net | CVE-2026-78661 | HIGH | v0.60.0 | 0.62.0 |

## Initial postgres image — 145 high/critical findings (resolved in replacement)

| Package | Advisory | Severity | Installed | Reported fix |
|---|---|---|---|---|
| bsdutils | CVE-2026-53613 | HIGH | 1:2.38.1-5+deb12u3 | Not reported |
| bsdutils | CVE-2026-53615 | HIGH | 1:2.38.1-5+deb12u3 | Not reported |
| bsdutils | CVE-2026-78410 | HIGH | 1:2.38.1-5+deb12u3 | Not reported |
| gzip | CVE-2026-41992 | HIGH | 1.12-1 | Not reported |
| libacl1 | CVE-2026-54369 | HIGH | 2.3.1-3 | Not reported |
| libblkid1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libblkid1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libblkid1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libfdisk1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libfdisk1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libfdisk1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libgssapi-krb5-2 | CVE-2026-107364 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112315 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112316 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112317 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112318 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112319 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112320 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112321 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112322 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-112323 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-118380 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-119079 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-71199 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libgssapi-krb5-2 | CVE-2026-71200 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-107364 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112315 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112316 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112317 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112318 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112319 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112320 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112321 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112322 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-112323 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-118380 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-119079 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-71199 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libk5crypto3 | CVE-2026-71200 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-107364 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112315 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112316 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112317 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112318 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112319 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112320 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112321 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112322 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-112323 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-118380 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-119079 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-71199 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5-3 | CVE-2026-71200 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-107364 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112315 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112316 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112317 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112318 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112319 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112320 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112321 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112322 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-112323 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-118380 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-119079 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-71199 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libkrb5support0 | CVE-2026-71200 | HIGH | 1.20.1-2+deb12u5 | Not reported |
| libldap-2.5-0 | CVE-2023-2953 | HIGH | 2.5.13+dfsg-5 | Not reported |
| libmount1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libmount1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libmount1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libncursesw6 | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| libpam-modules | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libpam-modules-bin | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libpam-runtime | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libpam0g | CVE-2025-6020 | HIGH | 1.5.2-6+deb12u2 | Not reported |
| libperl5.36 | CVE-2026-9538 | HIGH | 5.36.0-7+deb12u4 | Not reported |
| libsmartcols1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libsmartcols1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libsmartcols1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libsqlite3-0 | CVE-2025-7458 | CRITICAL | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-11822 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-11824 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-119373 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-119374 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libsqlite3-0 | CVE-2026-119379 | HIGH | 3.40.1-2+deb12u2 | Not reported |
| libssl3 | CVE-2026-107494 | HIGH | 3.0.22-1~deb12u2 | Not reported |
| libsystemd-shared | CVE-2026-16742 | HIGH | 252.39-1~deb12u2 | Not reported |
| libsystemd0 | CVE-2026-16742 | HIGH | 252.39-1~deb12u2 | Not reported |
| libtinfo6 | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| libudev1 | CVE-2026-16742 | HIGH | 252.39-1~deb12u2 | Not reported |
| libuuid1 | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libuuid1 | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libuuid1 | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| libxml2 | CVE-2026-6653 | CRITICAL | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| libxml2 | CVE-2026-74860 | HIGH | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| libxml2 | CVE-2026-86138 | HIGH | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| libxml2 | CVE-2026-86140 | HIGH | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| libxml2 | CVE-2026-86142 | HIGH | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| libxml2 | CVE-2026-86143 | HIGH | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| libxml2 | CVE-2026-86144 | HIGH | 2.9.14+dfsg-1.3~deb12u6 | Not reported |
| mount | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| mount | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| mount | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| ncurses-base | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| ncurses-bin | CVE-2025-69720 | HIGH | 6.4-4 | Not reported |
| openssl | CVE-2026-107494 | HIGH | 3.0.22-1~deb12u2 | Not reported |
| perl | CVE-2026-9538 | HIGH | 5.36.0-7+deb12u4 | Not reported |
| perl-base | CVE-2026-9538 | HIGH | 5.36.0-7+deb12u4 | Not reported |
| perl-modules-5.36 | CVE-2026-9538 | HIGH | 5.36.0-7+deb12u4 | Not reported |
| systemd | CVE-2026-16742 | HIGH | 252.39-1~deb12u2 | Not reported |
| util-linux | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux-extra | CVE-2026-53613 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux-extra | CVE-2026-53615 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| util-linux-extra | CVE-2026-78410 | HIGH | 2.38.1-5+deb12u3 | Not reported |
| zlib1g | CVE-2023-45853 | CRITICAL | 1:1.2.13.dfsg-1 | Not reported |
| zlib1g | CVE-2026-85091 | HIGH | 1:1.2.13.dfsg-1 | Not reported |
| stdlib | CVE-2025-68121 | CRITICAL | v1.24.6 | 1.24.13, 1.25.7, 1.26.0-rc.3 |
| stdlib | CVE-2025-61726 | HIGH | v1.24.6 | 1.24.12, 1.25.6 |
| stdlib | CVE-2025-61729 | HIGH | v1.24.6 | 1.24.11, 1.25.5 |
| stdlib | CVE-2026-111943 | HIGH | v1.24.6 | 1.26.10, 1.27.3 |
| stdlib | CVE-2026-25679 | HIGH | v1.24.6 | 1.25.8, 1.26.1 |
| stdlib | CVE-2026-27145 | HIGH | v1.24.6 | 1.25.11, 1.26.4 |
| stdlib | CVE-2026-32280 | HIGH | v1.24.6 | 1.25.9, 1.26.2 |
| stdlib | CVE-2026-32281 | HIGH | v1.24.6 | 1.25.9, 1.26.2 |
| stdlib | CVE-2026-32283 | HIGH | v1.24.6 | 1.25.9, 1.26.2 |
| stdlib | CVE-2026-33811 | HIGH | v1.24.6 | 1.25.10, 1.26.3 |
| stdlib | CVE-2026-33814 | HIGH | v1.24.6 | 1.25.10, 1.26.3 |
| stdlib | CVE-2026-33818 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-39820 | HIGH | v1.24.6 | 1.25.10, 1.26.3 |
| stdlib | CVE-2026-39821 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-39822 | HIGH | v1.24.6 | 1.25.12, 1.26.5, 1.27.0-rc.2 |
| stdlib | CVE-2026-39836 | HIGH | v1.24.6 | 1.25.10, 1.26.3 |
| stdlib | CVE-2026-42499 | HIGH | v1.24.6 | 1.25.10, 1.26.3 |
| stdlib | CVE-2026-42504 | HIGH | v1.24.6 | 1.25.11, 1.26.4 |
| stdlib | CVE-2026-56853 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-56858 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-56859 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-56860 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-56862 | HIGH | v1.24.6 | 1.25.13, 1.26.6, 1.27.0-rc.3 |
| stdlib | CVE-2026-78667 | HIGH | v1.24.6 | 1.26.9, 1.27.2 |
| stdlib | CVE-2026-78669 | HIGH | v1.24.6 | 1.26.9, 1.27.2 |
| stdlib | CVE-2026-97031 | HIGH | v1.24.6 | 1.26.9, 1.27.2 |

## Remediation status

The replacement web/database scans and fresh-volume runtime validation passed. The initial
web/database findings above are retained as historical evidence. The Caddy component has since been
replaced with a scanned and validated Traefik image; old-image findings remain historical. No feature or security control
was disabled to bypass a scan.

During migration, strict TLS validation rejected the first development certificate for
missing Authority Key Identifier. The generator was corrected to include issuer/subject
key identifiers; verification was never disabled. Corrected localhost TLS passed the live
proxy check. The invalid development artifacts are unused and remain protected/ignored.
No plaintext credentials, private keys or application responses were printed during diagnosis.

## Multi-campground review findings — 2026-11-24

The following integration risks were identified and corrected before production exposure:

- Default allauth email-confirmation HMAC signs a schema-local EmailAddress ID. Identical
  IDs in different schemas could accept another campground's confirmation link. The allauth
  settings hook now binds the salt to tenant UUID; identical-ID rejection and correct-tenant
  acceptance are tested. Reset tokens also bind UUID, including identical restored accounts.
- Django's content-type cache is keyed by DB alias, not PostgreSQL schema. Disabled retention
  through the mapping interface; regression tests verify isolation. Review on framework upgrades.
- A draft public-schema grant loop included platform operator events. Excluded their table
  and sequence and explicitly revoked app/migrator privileges. Actual runtime SELECT/sequence
  probes now return permission denial. No real production data or public deployment was involved.
- RLS permissive policies can combine with OR. Added a restrictive tenant guard so an additional
  permissive policy cannot erase the tenant condition; covered by a real PostgreSQL regression.
- Unscoped pg_dump is incompatible with forced tenant RLS. Updated the workflow to explicit
  registered UUID/schema context with --enable-row-security, INSERT-format data and encrypted
  registry metadata. Shell syntax passes; encrypted execution/restoration remains **unverified**.

Bandit B105 on ACCOUNT_PASSWORD_RESET_TOKEN_GENERATOR was reviewed as a false positive:
the literal is an allauth Python import path, not a credential or token. The single inline
B105 annotation documents that reason; no genuine finding or broad rule was suppressed.
Bandit otherwise passes. No security exception is requested or inferred.

The SaaS source Gitleaks scan and application image HIGH/CRITICAL scan passed. Existing
shared-process/host/key compromise and same-origin risks remain; no claim of isolation
against those actors is made. Backups/platform metadata recovery, aggregate load and the
remaining release acceptance gates are still open. Scans do not prove absence of vulnerabilities.

## Public-source import and mutation review — 2026-11-24

- The official linked `CAMPGROUND_RULES_2026.pdf`, page 1 Wi-Fi section, contains a network
  credential. Location: `https://georgiamountainfairgrounds.com/images/site/pageserver/image/otherevents/CAMPGROUND_RULES_2026.pdf`.
  Its value was excluded from fixtures, application assets, documentation, logs and summaries.
  No PDF asset was imported. Upstream publication/credential rotation remains the source
  owner's responsibility and is **unresolved externally**; no claim of upstream remediation.
- Conflicting published site totals and monthly lakeside rates are data-quality findings,
  not evidence of an application exploit. Inactive drafts, explicit reference-rate labels
  and server-side closed booking prevent them becoming unverified online inventory/charges.
- Mutation testing exposed coverage gaps in date types and stay boundaries, not an observed
  flaw in existing production date validation. Added meaningful regression cases. The first
  campaign killed 13/23; the second killed 19/23 with four reviewed survivors (three cosmetic
  message changes and one equivalent default range bound). No mutant was applied or excluded.
- Bandit subprocess findings were reviewed narrowly as documented in SD-024. No broad scan
  suppression or security-control bypass was introduced.

Release gates remain in force. No new application vulnerability is known from this review;
that statement does not imply exhaustive verification or production readiness.

## Image publishing review — 2026-11-24

The first local release snapshot inherited mode 0600/0700 from its private working directory.
Docker copied those modes into root-owned application files, preventing the non-root user
from reading source. Both-architecture execution checks caught the packaging failure before
any image was pushed. The snapshot now preserves ordinary readable source modes under an
unchanged 0700 parent workspace; secret files are excluded entirely. Added a regression test
for private workspace boundaries and image-readable source modes. Runtime privileges, secret
permissions and read-only filesystems were not relaxed. The failed candidates were not published.

The existing host Docker token could create repositories/push images but could not administer
repository visibility. After the owner's follow-up, all three repositories verified public. No broader token
permissions were requested by this task. Public source visibility is
an explicitly accepted confidentiality impact (SD-025), not an undisclosed regression. Current
per-architecture scans found no high/critical vulnerabilities or detected secrets; production
readiness and previously recorded external-source/release limitations remain unchanged.

## Public test banner/deployment review — 2026-11-24

No new application vulnerability was identified by the 196-test release run or current
source/image scans. The missing non-production visual identification and early error-path
coverage were addressed without changing authorization, TLS, DEBUG or other protections.
These are labeling/coverage improvements, not a claim that a prior exploitable vulnerability
was resolved. Host storage encryption, AWS firewall posture, recovery, renewal and production
release gates remain unverified until separately recorded. The test banner is not access control.

## Google implementation review — 2026-11-25

- Pre-release review found that denying all SocialToken permissions would break Django's
  account-unlink cascade. Runtime now has only SELECT/DELETE on that table; INSERT/UPDATE
  and sequence access remain denied. Client credential tables remain inaccessible.
  This was a draft implementation defect, not an observed deployed vulnerability.
- A candidate IPv4-mapped IPv6 ACL normalized to IPv4 /0 in Squid, inadvertently denying
  permitted Google access. The real network gate blocked publication. Corrected the ACL
  to use Squid's normalization with the existing private IPv4 ranges, and added DNS-to-
  mapped-metadata rejection checks. Allowed TLS and both metadata forms now pass their
  respective positive/negative tests; no private-target protection was removed.
- A negative snapshot-permission test assumed umask 022. The release run's umask 077
  exposed it. Explicitly set the intentionally invalid test directory mode; application
  secret/snapshot permissions remain unchanged. All 235 tests pass in the isolated release.
- Current source and both-architecture image scans report no HIGH/CRITICAL vulnerabilities
  or detected secrets. These are point-in-time automated results, not exhaustive assurance.
  The Google live human flow and existing production gates remain pending.

The approved Google/provider/egress trust impact is SD-027. No additional security exception
is pending. The previously documented upstream-published network credential is still an
external unresolved finding; its value is not copied into this repository.

## Interface release scan — 2026-11-25

Release `0.1.0-alpha.20261125-5815b9993895`: source and both-architecture web/DB/Traefik/egress
scans passed the HIGH/CRITICAL vulnerability gate and secret scans at build and publication.
Gitleaks source/deployment-bundle checks, Bandit and pip-audit passed. No new finding was
identified by these executed checks and no finding was suppressed or security waiver added.
No prior vulnerability is newly declared resolved by this presentation update. Lower-severity,
host, manual and remaining production acceptance reviews are not implied by this scan result.
