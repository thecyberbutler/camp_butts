# Mutation testing

The owner requested mutmut to find testing holes. Mutmut 3.8.1 is an exact development-only
Poetry dependency; runtime containers install only the main group. It modifies disposable
copies of reservation services to test whether the real PostgreSQL tests reject changed
behavior. It complements security regression/concurrency testing and dependency scanning;
a mutation score does not establish security or production readiness.

## Running a bounded campaign

Use the isolated synthetic PostgreSQL service configured by `scripts/provision_test_db.py`
and the protected local test credential described in README. Never point mutation testing
at production, a shared application database, or real camper data.

```sh
poetry install --with dev
.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 900
```

The default selector is `apps.reservations.services.x_date_range__mutmut_*`. A broader
reviewed reservation-service campaign can use:

```sh
.venv/bin/python scripts/mutation_test.py --port 55433 --timeout 7200 --selector 'apps.reservations.services.*'
```

The broader command is documented, **not claimed executed**. Resource/time limits may
require smaller function selectors. Do not run `mutmut apply` against application source.
Use a report's private source copy for `mutmut show` when reviewing a specific mutant.
Never copy a weakened mutant back into the application.

## Isolation and output protection

The wrapper validates the exact loopback synthetic DB identity and rejects superuser,
BYPASSRLS and CREATEROLE. It creates randomly named disposable databases and revokes PUBLIC
access, then drops only those generated names. It copies allowlisted source directories,
rejects symlinks, omits `.git`, `.secrets` and owner editor settings, and places artifacts
under ignored mode-0700 `.runtime/mutation/run-*`. A minimal subprocess environment carries
only a path to a protected test credential. Temporary test secrets are removed on exit.

Forkserver with no pre-fork warmup avoids inheriting open Django/crypto/database state;
there is one mutation worker. The full tests directory remains selected. The process group
is terminated on timeout/interruption, and the wrapper cleans its generated databases.
Raw subprocess output is discarded, not retained in logs: assertion/SQL failure diagnostics
could expose test secrets. Reports include only mutant identifiers, status counts and an
exit code. Inspect source diffs rather than enabling verbose diagnostics.

A nonzero wrapper exit means review is required. Survivors, internal errors, missing tests,
timeouts, unexecuted mutants and runner errors are not passes. In particular upstream exit
code 3 is reported as an internal error, not accepted as a kill. No survivor is silently
excluded. Keep private artifacts only as long as required for review.

## Initial findings

The first date-range campaign ran 23 mutants: **13 killed, 10 survived**. This exposed
missing tests for zero/91-night rejection, the valid 90-night ceiling, non-date arguments,
and meaningful validation guidance. Added boundary/type tests also explicitly verify
inclusive arrival/exclusive departure across leap day.

The subsequent campaign result is recorded in `implementation-progress.md`. Message casing
and added `XX` text are cosmetic survivors; omitting an explicit `[)` bounds argument is
equivalent because Psycopg defaults to those same bounds. These are reviewed limitations,
not suppressed mutants or reasons to weaken production validation. Campaign results cover
only this function, not the full reservation service or application.
