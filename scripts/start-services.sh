#!/bin/bash

# Start all services for PRD Analyst application

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_warning "Some commands may require sudo privileges"
fi

print_info "Starting PRD Analyst services..."

# Start PostgreSQL
print_info "Starting PostgreSQL..."
sudo systemctl start postgresql

# Start Backend
print_info "Starting Backend service..."
sudo systemctl start prd-backend

# Wait a bit for backend to initialize
sleep 2

# Start Frontend
print_info "Starting Frontend service..."
sudo systemctl start prd-frontend

# Wait for services to start
sleep 3

# Display status
echo ""
print_info "Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl status postgresql --no-pager -l | head -3
echo ""
sudo systemctl status prd-backend --no-pager -l | head -3
echo ""
sudo systemctl status prd-frontend --no-pager -l | head -3
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_info "All services started!"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "View logs:"
echo "  Backend: sudo journalctl -u prd-backend -f"
echo "  Frontend: sudo journalctl -u prd-frontend -f"
