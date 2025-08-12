# Backup and Restore Guide

This guide covers how to backup and restore The Commons database and configuration files for both development and production environments.

## Overview

The backup system supports both PostgreSQL and SQLite databases and automatically includes configuration files. Backups are stored in dated directories under `backups/`.

## Prerequisites

### For PostgreSQL Backups
- PostgreSQL client tools (`pg_dump`, `pg_restore`, `psql`)
- Access to the PostgreSQL server
- Environment variables configured (see below)

### For SQLite Backups
- No additional tools required (uses standard file operations)

## Environment Variables

### PostgreSQL Configuration
```bash
# Required for PostgreSQL backups
POSTGRES_PASSWORD=your_password

# Optional (defaults shown)
POSTGRES_USER=postgres
POSTGRES_DB=the_commons
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://user:pass@host:port/db
```

### SQLite Configuration
```bash
# Optional (defaults shown)
DB_FILE=test.db
```

## Backup Procedures

### Creating a Backup

Run the backup script from the project root:

```bash
# Make script executable (first time only)
chmod +x scripts/backup_db.sh

# Create backup
./scripts/backup_db.sh
```

The script will:
1. Create a backup directory: `backups/YYYY-MM-DD/`
2. Backup the database (PostgreSQL or SQLite)
3. Backup configuration files (`.env`, `docker-compose*.yml`)
4. Create a backup info file

### Backup Contents

Each backup directory contains:
- `db.dump` (PostgreSQL) or `db.sqlite` (SQLite) - Database backup
- `.env` - Environment configuration
- `docker-compose.yml` - Docker configuration
- `docker-compose.prod.yml` - Production Docker configuration
- `backup_info.txt` - Backup metadata

### Example Backup Output

```bash
$ ./scripts/backup_db.sh
[2024-01-15 10:30:00] Created backup directory: backups/2024-01-15
[2024-01-15 10:30:01] Backing up SQLite database...
[2024-01-15 10:30:01] SQLite backup completed: backups/2024-01-15/db.sqlite
[2024-01-15 10:30:01] Backing up configuration files...
[2024-01-15 10:30:01] Backed up .env
[2024-01-15 10:30:01] Backed up docker-compose.yml
[2024-01-15 10:30:01] Backup info written to: backups/2024-01-15/backup_info.txt
[2024-01-15 10:30:01] Backup completed successfully!
[2024-01-15 10:30:01] Backup location: backups/2024-01-15
[2024-01-15 10:30:01] Backup size: 2.1M
```

## Restore Procedures

### Restoring from Backup

Run the restore script from the project root:

```bash
# Make script executable (first time only)
chmod +x scripts/restore_db.sh

# Restore from backup (with confirmation)
./scripts/restore_db.sh backups/2024-01-15

# Restore without confirmation
./scripts/restore_db.sh backups/2024-01-15 --force

# Dry run (see what would be restored)
./scripts/restore_db.sh backups/2024-01-15 --dry-run
```

### Restore Process

The restore script will:
1. Validate the backup directory exists
2. Show backup information
3. Confirm the restore (unless `--force` is used)
4. Stop the application (if running)
5. Restore the database
6. Restore configuration files
7. Restart the application
8. Validate the restore

### Example Restore Output

```bash
$ ./scripts/restore_db.sh backups/2024-01-15
[2024-01-15 11:00:00] Starting database restore from: backups/2024-01-15
[2024-01-15 11:00:00] Backup information:
  Backup created: Mon Jan 15 10:30:01 UTC 2024
  Database type: SQLite
  Database file: test.db
[2024-01-15 11:00:00] Are you sure you want to restore the database? This will overwrite the current data. (y/N): y
[2024-01-15 11:00:01] Restoring SQLite database...
[2024-01-15 11:00:01] Stopping application...
[2024-01-15 11:00:02] Backing up current database to test.db.backup.20240115_110002
[2024-01-15 11:00:02] Restoring database from backup...
[2024-01-15 11:00:02] SQLite restore completed successfully
[2024-01-15 11:00:03] Restarting application...
[2024-01-15 11:00:03] Restoring configuration files...
[2024-01-15 11:00:03] Restored .env
[2024-01-15 11:00:03] Validating restore...
[2024-01-15 11:00:03] SQLite restore validation successful
[2024-01-15 11:00:03] Restore completed successfully!
```

## Development Environment

### Local Development with SQLite

```bash
# Backup local development database
./scripts/backup_db.sh

# Restore to local development
./scripts/restore_db.sh backups/2024-01-15
```

### Local Development with PostgreSQL

```bash
# Set PostgreSQL environment variables
export POSTGRES_PASSWORD=your_local_password
export POSTGRES_DB=the_commons_dev

# Backup
./scripts/backup_db.sh

# Restore
./scripts/restore_db.sh backups/2024-01-15
```

## Production Environment

### Production Backup

```bash
# Set production environment variables
export POSTGRES_PASSWORD=your_production_password
export POSTGRES_HOST=your_production_host
export POSTGRES_DB=the_commons_prod

# Create backup
./scripts/backup_db.sh

# Optional: Copy backup to secure location
rsync -av backups/2024-01-15/ backup-server:/backups/the-commons/
```

### Production Restore

```bash
# Set production environment variables
export POSTGRES_PASSWORD=your_production_password
export POSTGRES_HOST=your_production_host
export POSTGRES_DB=the_commons_prod

# Restore (use --force to skip confirmation in automated scripts)
./scripts/restore_db.sh backups/2024-01-15 --force
```

## Automated Backups

### Cron Job Setup

Add to your crontab for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/the-commons && ./scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### Docker Compose Backup

For Docker environments, you can run backups from outside the container:

```bash
# Backup from host
docker-compose exec -T db pg_dump -U postgres the_commons > backup.sql

# Or use the backup script with proper environment
docker-compose exec -T app ./scripts/backup_db.sh
```

## Troubleshooting

### Common Issues

**PostgreSQL connection failed**
- Check environment variables are set correctly
- Verify PostgreSQL server is running
- Ensure user has proper permissions

**SQLite file not found**
- Check `DB_FILE` environment variable
- Verify the database file exists in the expected location

**Permission denied**
- Make sure scripts are executable: `chmod +x scripts/*.sh`
- Check file permissions on backup directory

**Restore validation failed**
- Check database connection
- Verify backup file integrity
- Review application logs for errors

### Backup Verification

```bash
# Check backup contents
ls -la backups/2024-01-15/

# Verify backup info
cat backups/2024-01-15/backup_info.txt

# Test restore with dry run
./scripts/restore_db.sh backups/2024-01-15 --dry-run
```

### Log Files

Backup and restore operations log to:
- Console output (with timestamps)
- Application logs (if running)
- System logs (if using cron)

## Security Considerations

- Store backup files securely
- Use encrypted connections for PostgreSQL
- Limit access to backup directories
- Rotate backup files regularly
- Test restore procedures periodically
- Keep backup scripts and documentation updated

## Best Practices

1. **Regular Backups**: Schedule daily backups
2. **Test Restores**: Periodically test restore procedures
3. **Multiple Locations**: Store backups in multiple locations
4. **Version Control**: Keep backup scripts in version control
5. **Documentation**: Document any custom backup procedures
6. **Monitoring**: Monitor backup success/failure
7. **Retention**: Implement backup retention policies
