#!/bin/bash

# PostgreSQL setup script
# This script initializes the PostgreSQL database for the PRD Analyst application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Database configuration
DB_NAME="prd"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Get project directory
PROJECT_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
SCHEMA_FILE="$PROJECT_DIR/backend/database/schema.sql"

print_info "Setting up PostgreSQL database..."

# Start PostgreSQL service
systemctl start postgresql
systemctl enable postgresql

# Wait for PostgreSQL to be ready
sleep 2

# Check if database exists
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

if [ "$DB_EXISTS" = "1" ]; then
    print_info "Database '$DB_NAME' already exists"
else
    print_info "Creating database '$DB_NAME'..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
fi

# Set password for postgres user
print_info "Setting password for postgres user..."
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Import schema
if [ -f "$SCHEMA_FILE" ]; then
    print_info "Importing database schema..."
    sudo -u postgres psql -d $DB_NAME -f "$SCHEMA_FILE"
    print_info "Schema imported successfully"
else
    print_error "Schema file not found: $SCHEMA_FILE"
    exit 1
fi

# Configure PostgreSQL to accept local connections
print_info "Configuring PostgreSQL authentication..."
PG_HBA="/etc/postgresql/14/main/pg_hba.conf"
if grep -q "host.*all.*all.*127.0.0.1/32.*md5" "$PG_HBA"; then
    print_info "PostgreSQL already configured for local connections"
else
    echo "host    all             all             127.0.0.1/32            md5" >> "$PG_HBA"
    systemctl restart postgresql
    print_info "PostgreSQL configured and restarted"
fi

print_info "PostgreSQL setup completed successfully!"
print_info "Database: $DB_NAME"
print_info "User: $DB_USER"
print_info "Connection string: postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
