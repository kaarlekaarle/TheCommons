#!/bin/bash

# Create backups directory if it doesn't exist
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

# Generate timestamp for backup name
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="project_backup_$TIMESTAMP"

# Create temporary directory for backup
TEMP_DIR=$(mktemp -d)

# Copy project files to temporary directory, excluding unnecessary files
rsync -av --progress . "$TEMP_DIR/$BACKUP_NAME" \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude 'backups' \
    --exclude '*.log' \
    --exclude '.env' \
    --exclude '.DS_Store' \
    --exclude 'dist' \
    --exclude 'build' \
    --exclude 'coverage'

# Create compressed archive
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$TEMP_DIR" "$BACKUP_NAME"

# Clean up temporary directory
rm -rf "$TEMP_DIR"

# Keep only the last 3 backups
ls -t "$BACKUP_DIR"/*.tar.gz | tail -n +4 | xargs -r rm

echo "Backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz" 