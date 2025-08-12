#!/bin/bash

# Restore script for The Commons database
# Supports both PostgreSQL and SQLite databases

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Configuration
DB_FILE="${DB_FILE:-test.db}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_DB="${POSTGRES_DB:-the_commons}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# Function to show usage
usage() {
    echo "Usage: $0 <backup_directory> [options]"
    echo ""
    echo "Arguments:"
    echo "  backup_directory    Path to the backup directory (e.g., backups/2024-01-15)"
    echo ""
    echo "Options:"
    echo "  --dry-run          Show what would be restored without actually restoring"
    echo "  --force            Skip confirmation prompts"
    echo "  --help             Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  DB_FILE            SQLite database file path (default: test.db)"
    echo "  POSTGRES_*         PostgreSQL connection parameters"
    echo ""
    echo "Examples:"
    echo "  $0 backups/2024-01-15"
    echo "  $0 backups/2024-01-15 --dry-run"
    echo "  $0 backups/2024-01-15 --force"
}

# Function to restore PostgreSQL
restore_postgres() {
    local backup_dir="$1"
    local dry_run="$2"
    
    log "Restoring PostgreSQL database..."
    
    # Check if pg_restore is available
    if ! command -v pg_restore &> /dev/null; then
        error "pg_restore not found. Please install PostgreSQL client tools."
        exit 1
    fi
    
    # Check if backup file exists
    local backup_file="$backup_dir/db.dump"
    if [ ! -f "$backup_file" ]; then
        error "PostgreSQL backup file not found: $backup_file"
        exit 1
    fi
    
    if [ "$dry_run" = "true" ]; then
        log "DRY RUN: Would restore from $backup_file to database $POSTGRES_DB"
        return 0
    fi
    
    # Set PGPASSWORD if provided
    if [ -n "$POSTGRES_PASSWORD" ]; then
        export PGPASSWORD="$POSTGRES_PASSWORD"
    fi
    
    # Drop and recreate database
    log "Dropping existing database..."
    dropdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" --if-exists "$POSTGRES_DB" || true
    
    log "Creating new database..."
    createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$POSTGRES_DB"
    
    # Restore from backup
    log "Restoring database from backup..."
    pg_restore -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$backup_file"
    
    if [ $? -eq 0 ]; then
        log "PostgreSQL restore completed successfully"
    else
        error "PostgreSQL restore failed"
        exit 1
    fi
}

# Function to restore SQLite
restore_sqlite() {
    local backup_dir="$1"
    local dry_run="$2"
    
    log "Restoring SQLite database..."
    
    # Check if backup file exists
    local backup_file="$backup_dir/db.sqlite"
    if [ ! -f "$backup_file" ]; then
        error "SQLite backup file not found: $backup_file"
        exit 1
    fi
    
    if [ "$dry_run" = "true" ]; then
        log "DRY RUN: Would restore from $backup_file to $DB_FILE"
        return 0
    fi
    
    # Stop the application if it's running
    log "Stopping application..."
    if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
        docker-compose down || true
    fi
    
    # Backup current database if it exists
    if [ -f "$DB_FILE" ]; then
        local current_backup="${DB_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        log "Backing up current database to $current_backup"
        cp "$DB_FILE" "$current_backup"
    fi
    
    # Restore from backup
    log "Restoring database from backup..."
    cp "$backup_file" "$DB_FILE"
    
    if [ $? -eq 0 ]; then
        log "SQLite restore completed successfully"
    else
        error "SQLite restore failed"
        exit 1
    fi
    
    # Restart the application
    log "Restarting application..."
    if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
        docker-compose up -d || true
    fi
}

# Function to validate restore
validate_restore() {
    local backup_dir="$1"
    local dry_run="$2"
    
    if [ "$dry_run" = "true" ]; then
        log "DRY RUN: Would validate restore"
        return 0
    fi
    
    log "Validating restore..."
    
    # Check if we have a PostgreSQL or SQLite backup
    if [ -f "$backup_dir/db.dump" ]; then
        # PostgreSQL validation
        if command -v psql &> /dev/null; then
            if [ -n "$POSTGRES_PASSWORD" ]; then
                export PGPASSWORD="$POSTGRES_PASSWORD"
            fi
            
            # Simple query to test connection
            if psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" &> /dev/null; then
                log "PostgreSQL restore validation successful"
            else
                warn "PostgreSQL restore validation failed"
            fi
        fi
    elif [ -f "$backup_dir/db.sqlite" ]; then
        # SQLite validation
        if command -v sqlite3 &> /dev/null && [ -f "$DB_FILE" ]; then
            if sqlite3 "$DB_FILE" "SELECT 1;" &> /dev/null; then
                log "SQLite restore validation successful"
            else
                warn "SQLite restore validation failed"
            fi
        fi
    fi
}

# Function to restore configuration
restore_config() {
    local backup_dir="$1"
    local dry_run="$2"
    
    log "Restoring configuration files..."
    
    # Restore .env if it exists in backup
    if [ -f "$backup_dir/.env" ]; then
        if [ "$dry_run" = "true" ]; then
            log "DRY RUN: Would restore .env from backup"
        else
            cp "$backup_dir/.env" ".env"
            log "Restored .env"
        fi
    fi
    
    # Restore docker-compose files if they exist in backup
    if [ -f "$backup_dir/docker-compose.yml" ]; then
        if [ "$dry_run" = "true" ]; then
            log "DRY RUN: Would restore docker-compose.yml from backup"
        else
            cp "$backup_dir/docker-compose.yml" "docker-compose.yml"
            log "Restored docker-compose.yml"
        fi
    fi
    
    if [ -f "$backup_dir/docker-compose.prod.yml" ]; then
        if [ "$dry_run" = "true" ]; then
            log "DRY RUN: Would restore docker-compose.prod.yml from backup"
        else
            cp "$backup_dir/docker-compose.prod.yml" "docker-compose.prod.yml"
            log "Restored docker-compose.prod.yml"
        fi
    fi
}

# Main restore logic
main() {
    local backup_dir=""
    local dry_run="false"
    local force="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --force)
                force="true"
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            -*)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [ -z "$backup_dir" ]; then
                    backup_dir="$1"
                else
                    error "Multiple backup directories specified"
                    usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Check if backup directory is provided
    if [ -z "$backup_dir" ]; then
        error "Backup directory is required"
        usage
        exit 1
    fi
    
    # Check if backup directory exists
    if [ ! -d "$backup_dir" ]; then
        error "Backup directory does not exist: $backup_dir"
        exit 1
    fi
    
    log "Starting database restore from: $backup_dir"
    
    # Show backup info if available
    if [ -f "$backup_dir/backup_info.txt" ]; then
        log "Backup information:"
        cat "$backup_dir/backup_info.txt" | sed 's/^/  /'
        echo
    fi
    
    # Confirm restore unless --force is used
    if [ "$force" != "true" ] && [ "$dry_run" != "true" ]; then
        echo -n "Are you sure you want to restore the database? This will overwrite the current data. (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Restore cancelled"
            exit 0
        fi
    fi
    
    # Determine database type and restore accordingly
    if [ -f "$backup_dir/db.dump" ]; then
        restore_postgres "$backup_dir" "$dry_run"
    elif [ -f "$backup_dir/db.sqlite" ]; then
        restore_sqlite "$backup_dir" "$dry_run"
    else
        error "No database backup found in $backup_dir"
        exit 1
    fi
    
    # Restore configuration
    restore_config "$backup_dir" "$dry_run"
    
    # Validate restore
    validate_restore "$backup_dir" "$dry_run"
    
    if [ "$dry_run" = "true" ]; then
        log "DRY RUN: Restore simulation completed"
    else
        log "Restore completed successfully!"
    fi
}

# Run main function
main "$@"
