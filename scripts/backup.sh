#!/bin/bash

# Configuration
PROJECT_DIR="/home/ubuntu/tim6_prd_workdir"
BACKUP_DIR="$PROJECT_DIR/backup"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting backup process..."

# 1. Backup Database
echo "Backing up 'prd' database..."
# Use sudo -u postgres to bypass password auth issues if running as ubuntu user
if sudo -u postgres pg_dump -C -d prd > "$BACKUP_DIR/prd_backup.sql"; then
    echo "Database backup successful."
else
    echo "Error: Database backup failed!"
    exit 1
fi

# 2. Backup Configuration Files (.env)
echo "Backing up configuration files..."
if [ -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env" "$BACKUP_DIR/.env.root"
    echo "Saved root .env"
else
    echo "Warning: $PROJECT_DIR/.env not found"
fi

if [ -f "$PROJECT_DIR/backend/.env" ]; then
    cp "$PROJECT_DIR/backend/.env" "$BACKUP_DIR/.env.backend"
    echo "Saved backend/.env"
else
    echo "Warning: $PROJECT_DIR/backend/.env not found"
fi

# 3. Backup Nginx Configs (if they exist in workspace)
echo "Backing up Nginx configs..."
if [ -f "$PROJECT_DIR/nginx.conf" ]; then
    cp "$PROJECT_DIR/nginx.conf" "$BACKUP_DIR/nginx.conf"
fi
if [ -f "$PROJECT_DIR/nextjs-nginx.conf" ]; then
    cp "$PROJECT_DIR/nextjs-nginx.conf" "$BACKUP_DIR/nextjs-nginx.conf"
fi

# 4. Verify
echo "Backup saved to: $BACKUP_DIR"
ls -lh "$BACKUP_DIR"
