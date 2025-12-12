#!/bin/bash

# Configuration
PROJECT_DIR="/home/ubuntu/tim6_prd_workdir"
BACKUP_DIR="$PROJECT_DIR/backup"

echo "Starting restore process..."

# Check backup directory
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory $BACKUP_DIR not found!"
    exit 1
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "Error: 'psql' command not found."
    echo "It seems PostgreSQL is not installed (common after a RunPod restart)."
    echo "Please run './setup.sh' (or 'scripts/setup-local-postgres.sh') first to reinstall system dependencies."
    exit 1
fi

# 1. Restore Config Files
echo "Restoring configuration files..."
if [ -f "$BACKUP_DIR/.env.root" ]; then
    cp "$BACKUP_DIR/.env.root" "$PROJECT_DIR/.env"
    echo "Restored root .env"
fi

if [ -f "$BACKUP_DIR/.env.backend" ]; then
    cp "$BACKUP_DIR/.env.backend" "$PROJECT_DIR/backend/.env"
    echo "Restored backend/.env"
fi

# 2. Restore Database
echo "Restoring database..."

# Ensure Postgres is running
if ! systemctl is-active --quiet postgresql; then
    echo "PostgreSQL service is not active. Attempting to start..."
    sudo service postgresql start
    sleep 5
fi

# Drop existing 'prd' database to ensure clean restore (The dump was created with -C so it includes CREATE DATABASE)
echo "Dropping existing 'prd' database if it exists..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS prd;"

echo "Importing database dump..."
if sudo -u postgres psql -f "$BACKUP_DIR/prd_backup.sql"; then
    echo "Database restore successful."
else
    echo "Error: Database restore failed!"
    exit 1
fi

# 3. Restore Nginx Configs (Copy back to workspace, User still needs to symlink if system was wiped)
echo "Restoring Nginx configs to workspace..."
if [ -f "$BACKUP_DIR/nginx.conf" ]; then
    cp "$BACKUP_DIR/nginx.conf" "$PROJECT_DIR/nginx.conf"
fi
if [ -f "$BACKUP_DIR/nextjs-nginx.conf" ]; then
    cp "$BACKUP_DIR/nextjs-nginx.conf" "$PROJECT_DIR/nextjs-nginx.conf"
fi

echo "Restore complete."
echo "Note: If system packages (like nginx, postgresql) were wiped, you need to reinstall them first."
echo "You may also need to reinstall node_modules or python venv if they were deleted."
