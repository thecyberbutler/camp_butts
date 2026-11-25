# Backup and restoration

Backup artifacts contain personal data, password hashes, encrypted MFA and sessions.
Use restic encryption, a separately protected repository key, encrypted host disks and
an offline/off-host copy. Docker volumes and Compose secrets are not encryption.
Never store the backup password beside the repository without independent protection.

## Backup workflow

Install a reviewed supported restic and PostgreSQL client on the protected backup host.
Provision a separate backup login with CONNECT, schema USAGE and SELECT on required
tables in the selected campground schema (including audit and migration history),
SELECT on the public tenant directory, and no schema/role administration. Never grant
SUPERUSER, BYPASSRLS or membership in a privileged role to the backup identity. Restrict its network
path; do not publish PostgreSQL publicly. Configure libpq service/password files as 0600.
Use a private network with verified TLS for remote-host database access. `PGSERVICEFILE`
must define `campground_backup`; `PGPASSFILE` holds its password. Secrets stay out of args.

Set RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE, PGSERVICEFILE, PGPASSFILE,
BACKUP_CONFIG_DIR, BACKUP_MEDIA_DIR, BACKUP_TENANT_ID and BACKUP_TENANT_SCHEMA, then run `bash scripts/backup.sh`. Initialize
the repository with `restic init` under the same protected configuration first. The script
validates the UUID/schema binding, nonprivileged backup role, active row security and
forced row-security flags. It selects only that schema with transaction context supplied by
libpq PGOPTIONS, uses pg_dump --enable-row-security --inserts, and streams the custom dump
directly into restic encryption. A separate encrypted metadata snapshot records the original
UUID/schema/directory binding. Platform directory/event tables and the operator event sequence
are excluded from the tenant dump. Pipeline failure prevents a completed-set message; partial
snapshots are not complete backups. Configuration/media are separately encrypted with the
same tenant-specific timestamp tag, followed by restic integrity checks. Treat a set as complete only if every step succeeds. Do not include plaintext
secret files in the ordinary config directory; escrow signing/MFA/session recovery keys
separately under independent encryption and restricted access.

Schedule nightly with cron/systemd and alert on nonzero exit. Example retention policy
for owner review: 7 daily, 4 weekly and 6 monthly complete sets. Apply `restic forget`
and `prune` only after reviewing recoverability and retention obligations. Avoid destroying
the last known-good backup. Database/media consistency requires quiescing media changes;
uploads are not exposed in this version. Backup-role provisioning and automated retention
are not yet integrated into Compose.

## Isolated restore drill

`CONFIRM_ISOLATED_RESTORE=YES bash scripts/restore.sh SNAPSHOT /new/protected/staging`
restores only into a new directory and verifies files. It refuses an existing destination.
Restore both database and asset snapshots from the same completed backup set.

On a separate replacement/validation host, provision new runtime/migration/admin
credentials and isolated volumes. Restore the dump into an explicitly selected empty
database with `pg_restore --no-owner --no-acl`, using the controlled migration identity
and btree_gist preinstalled in campground_extensions. Restore the original tenant UUID/schema
mapping from encrypted metadata as inactive through a reviewed operator process; do not assign
another tenant's identity to the data. Enter that UUID context for data-only restores under RLS;
use --enable-row-security and the INSERT-based dump, never disable RLS to make restoration work.
Apply current migrations and protections/grants under the original tenant context before activation. Restore required MFA encryption material from separate escrow.
Do not overwrite a running production database. Require explicit owner confirmation
before any destructive replacement.

Before opening access, delete restored sessions through the controlled administrative
process, rotate signing/session keys, invalidate pending invitations/reset/verification
material as appropriate, review historical account privileges and recovered MFA state,
reapply least-privilege grants, run migrations, tests and deployment checks, and verify
occupancy, MFA and object authorization. Restoring old credentials may revive compromised
security state; investigate before trusting it. Document recovery timing and evidence.

Status: scripts exist; encrypted backup/restore and recovery-time drills have **not** been
executed. This remains a release gate. Do not treat a successful pg_dump alone as recovery
validation.

Traefik ACME storage contains TLS private keys and the ACME account key. Back it up only
under encryption with restricted access; keep it outside ordinary non-secret configuration
copies. Restore into a protected 0700 volume with `acme.json` mode 0600 and the correct
non-root owner. Local development CA/leaf material is separate and must never replace
production certificate state. Legacy Caddy volumes remain sensitive after migration.


## SaaS recovery gaps and release gates

Schedule/verify each tenant separately. Use only that tenant's configuration/media directories
for tenant snapshots, never another campground's assets or a shared secret directory. Quiesce
provisioning/migration/media changes while making a consistent backup set. The script checks
schema/role context but does not prove every expected row was dumped; restore drills must
compare table counts, known synthetic account/MFA state and occupancy constraints per tenant.

The host backup environment requires reviewed psql, pg_dump and restic executables. The updated
script has shell syntax validation only; encrypted end-to-end execution, row-count checks,
restore/retention automation and recovery-time objectives are unverified. Separate encrypted
platform directory/operator-event archival and recovery are still required. Do not claim that
per-tenant snapshots alone provide complete platform disaster recovery. Shared application
signing/MFA/session keys require independent escrow; an encrypted database without them is
not a complete recovery set. These gaps block production release.

## Imported profile state

Tenant backups include public profile fields, source-import digest, inactive draft sites
and the booking-closure switch. Restore their values together and verify closure/inactive
counts before routing traffic. Do not use a repeated or changed initial import as a backup
restore mechanism. Mutation databases and ignored `.runtime/mutation` artifacts are
disposable synthetic test state and are excluded from application recovery. The encrypted
restore rehearsal remains required and is not claimed completed by the import tests.

## Registry image recovery

Retain the verified release image digest lock with protected deployment records. Registry
images contain code only and are not backups of campsite/account/reservation data, secrets
or certificate state. Restore still requires the encrypted database/platform metadata and
separately protected keys. Use compatible image digests and original ownership; do not
replace restored data permissions with broad access to fit a prebuilt image.

The public AWS development project's fresh volumes/secrets belong only to `camp-butts-test`.
No production data or local development database is copied there. Until encrypted recovery
is rehearsed and host storage encryption verified, use synthetic test data only. A deployment
failure or rollback must preserve volumes and protected secret files; never use `down -v`
as a troubleshooting shortcut. Certificate state is confidential backup material too.

## Google enablement snapshot

The AWS first-enable script streams `pg_dump --format=custom` directly to established Fernet
encryption, with a 64 MiB bound and no plaintext dump file. It uses the existing operator DB
credential only in the DB container, never runtime permission expansion. The 0600 key is
inside `/root/camp-butts-google-recovery`; ciphertext and prior digest lock are in
`/opt/camp-butts-test/pre-google-snapshot`. Separate 0700 directories protect both; key access
remains a host-root trust boundary. Authenticated decryption is checked without printing data.

This is a pre-upgrade database recovery aid, not complete disaster recovery: key and snapshot
remain on one host, no off-host escrow or restore drill is claimed, and TLS/application/OAuth
secret files require independent protected recovery. Preserve the new Google credential file
without including it in ordinary deployment bundles. Never dump/print keys to recover. A
restore must target a separately reviewed isolated database and preserve original tenant
identities and constraints; destructive live replacement requires owner authorization.
