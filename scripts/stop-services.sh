#!/bin/bash

# Stop all services for PRD Analyst application

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
    exit 1
fi

print_info "Stopping PRD Analyst services..."

# Stop Frontend
print_info "Stopping Frontend service..."
systemctl stop prd-frontend || true

# Stop Backend
print_info "Stopping Backend service..."
systemctl stop prd-backend || true

# Optionally stop PostgreSQL (commented out by default)
# print_info "Stopping PostgreSQL..."
# systemctl stop postgresql

echo ""
print_info "All services stopped!"
echo ""
echo "To restart services, run:"
echo "  sudo bash scripts/start-services.sh"
