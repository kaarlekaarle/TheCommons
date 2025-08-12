#!/bin/bash

# Backup script for The Commons database
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
BACKUP_DIR="backups/$(date +%F)"
DB_FILE="${DB_FILE:-test.db}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_DB="${POSTGRES_DB:-the_commons}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# Create backup directory
mkdir -p "$BACKUP_DIR"
log "Created backup directory: $BACKUP_DIR"

# Function to backup PostgreSQL
backup_postgres() {
    log "Backing up PostgreSQL database..."
    
    # Check if pg_dump is available
    if ! command -v pg_dump &> /dev/null; then
        error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi
    
    # Set PGPASSWORD if provided
    if [ -n "$POSTGRES_PASSWORD" ]; then
        export PGPASSWORD="$POSTGRES_PASSWORD"
    fi
    
    # Create backup
    pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "$BACKUP_DIR/db.dump"
    
    if [ $? -eq 0 ]; then
        log "PostgreSQL backup completed: $BACKUP_DIR/db.dump"
    else
        error "PostgreSQL backup failed"
        exit 1
    fi
}

# Function to backup SQLite
backup_sqlite() {
    log "Backing up SQLite database..."
    
    # Check if database file exists
    if [ ! -f "$DB_FILE" ]; then
        warn "SQLite database file not found: $DB_FILE"
        return 0
    fi
    
    # Create backup
    cp "$DB_FILE" "$BACKUP_DIR/db.sqlite"
    
    if [ $? -eq 0 ]; then
        log "SQLite backup completed: $BACKUP_DIR/db.sqlite"
    else
        error "SQLite backup failed"
        exit 1
    fi
}

# Function to backup configuration files
backup_config() {
    log "Backing up configuration files..."
    
    # Backup .env if it exists
    if [ -f ".env" ]; then
        cp ".env" "$BACKUP_DIR/.env"
        log "Backed up .env"
    else
        warn ".env file not found"
    fi
    
    # Backup docker-compose files
    if [ -f "docker-compose.yml" ]; then
        cp "docker-compose.yml" "$BACKUP_DIR/docker-compose.yml"
        log "Backed up docker-compose.yml"
    fi
    
    if [ -f "docker-compose.prod.yml" ]; then
        cp "docker-compose.prod.yml" "$BACKUP_DIR/docker-compose.prod.yml"
        log "Backed up docker-compose.prod.yml"
    fi
    
    # Create backup info file
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Database type: $([ -n "${POSTGRES_PASSWORD:-}" ] && echo "PostgreSQL" || echo "SQLite")
Database file: $DB_FILE
PostgreSQL config:
  Host: $POSTGRES_HOST
  Port: $POSTGRES_PORT
  User: $POSTGRES_USER
  Database: $POSTGRES_DB
EOF
    
    log "Backup info written to: $BACKUP_DIR/backup_info.txt"
}

# Main backup logic
main() {
    log "Starting database backup..."
    
    # Determine database type and backup accordingly
    if [ -n "${POSTGRES_PASSWORD:-}" ] || [ -n "${DATABASE_URL:-}" ]; then
        backup_postgres
    else
        backup_sqlite
    fi
    
    # Always backup configuration
    backup_config
    
    log "Backup completed successfully!"
    log "Backup location: $BACKUP_DIR"
    
    # Show backup size
    if [ -d "$BACKUP_DIR" ]; then
        total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
        log "Backup size: $total_size"
    fi
}

# Run main function
main "$@"
