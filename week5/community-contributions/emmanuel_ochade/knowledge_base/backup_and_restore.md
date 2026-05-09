# Backup and Restore

## Database backup

- **Schedule:** Full backup daily at 02:00 UTC. Incremental backups every 6 hours.
- **Destination:** Object storage bucket `s3://company-db-backups/`. Retention: 30 days.
- **Manual backup:** Run `./scripts/backup_db.sh`. It dumps the database and uploads to the bucket with a timestamped filename.

## Restore from backup

1. List available backups: `aws s3 ls s3://company-db-backups/`.
2. Download the chosen backup and stop the application that uses the DB.
3. Restore: `psql -U postgres -d app_db < backup_YYYYMMDD.sql` (or use your DB client).
4. Run migrations if the backup is from an older version: `alembic upgrade head`.
5. Restart the application and run smoke tests.

## Config and secrets

- Config files and secrets are stored in a secrets manager. Backups are automatic; restore is done via the same manager’s UI or CLI.
- Do not store production secrets in runbooks or code.
