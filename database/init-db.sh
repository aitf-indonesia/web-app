#!/bin/bash
set -e

# Database initialization script for Docker
# This script runs automatically when the PostgreSQL container starts for the first time
# It initializes the database schema and optionally loads data

echo "========================================="
echo "PRD Database Initialization"
echo "========================================="

# Check if database is already initialized
if [ -z "$(psql -U postgres -d prd -c '\dt' 2>/dev/null)" ]; then
    echo "✓ Database is empty, initializing..."
    
    # Initialize schema
    if [ -f /docker-entrypoint-initdb.d/init-schema.sql ]; then
        echo "→ Creating database schema..."
        psql -U postgres -d prd < /docker-entrypoint-initdb.d/init-schema.sql
        echo "✓ Schema created successfully!"
    else
        echo "✗ Schema file not found!"
        exit 1
    fi
    
    # Load data (optional)
    if [ -f /docker-entrypoint-initdb.d/init-data.sql ]; then
        echo "→ Loading initial data..."
        psql -U postgres -d prd < /docker-entrypoint-initdb.d/init-data.sql
        echo "✓ Data loaded successfully!"
    else
        echo "⚠ Data file not found!"
        echo "  Database will have schema only (no initial data)"
    fi
    
else
    echo "✓ Database already initialized, skipping..."
fi

echo "========================================="
echo "Database initialization complete!"
echo "========================================="
