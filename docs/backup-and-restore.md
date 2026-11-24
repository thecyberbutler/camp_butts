# Backup and restoration

Backup artifacts contain personal data, password hashes, encrypted MFA and sessions.
Use restic encryption, a separately protected repository key, encrypted host disks and
an offline/off-host copy. Docker volumes and Compose secrets are not encryption.
Never store the backup password beside the repository without independent protection.

## Backup workflow

Install a reviewed supported restic and PostgreSQL client on the protected backup host.
Provision a separate backup login with CONNECT, schema USAGE and SELECT on required
application tables (including audit), no schema/role administration. Restrict its network
path; do not publish PostgreSQL publicly. Configure libpq service/password files as 0600.
Use a private network with verified TLS for remote-host database access. `PGSERVICEFILE`
must define `campground_backup`; `PGPASSFILE` holds its password. Secrets stay out of args.

Set RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE, PGSERVICEFILE, PGPASSFILE,
BACKUP_CONFIG_DIR and BACKUP_MEDIA_DIR, then run `bash scripts/backup.sh`. Initialize
the repository with `restic init` under the same protected configuration first. The script
streams pg_dump directly into encryption and checks both pipeline exits, backs up
configuration/media separately under a common timestamp tag, then runs restic integrity
checks. Treat a set as complete only if every step succeeds. Do not include plaintext
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
and preinstalled btree_gist. Restore required MFA encryption material from separate escrow.
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
