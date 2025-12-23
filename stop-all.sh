#!/bin/bash
# Stop all services

echo "========================================="
echo "Stopping All Services"
echo "========================================="

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env 2>/dev/null || true
    set +a
fi

# Get ports from environment or use defaults
FRONTEND_PORT=${FRONTEND_PORT:-3000}
BACKEND_PORT=${BACKEND_PORT:-8000}
INTEGRASI_PORT=${SERVICE_API_PORT:-5000}

echo "→ Stopping Frontend (port $FRONTEND_PORT)..."
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || echo "  Frontend not running"

echo "→ Stopping Backend (port $BACKEND_PORT)..."
lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || echo "  Backend not running"

echo "→ Stopping Integrasi Service (port $INTEGRASI_PORT)..."
lsof -ti:$INTEGRASI_PORT | xargs kill -9 2>/dev/null || echo "  Integrasi Service not running"

# Also kill by process name (fallback)
echo "→ Cleaning up remaining processes..."
pkill -f "next dev" 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "python main_api.py" 2>/dev/null || true

echo "→ Stopping Backup Service..."
pkill -f "backup_db.sh" 2>/dev/null || echo "  Backup Service not running"

echo ""
echo "✓ All services stopped"
echo ""
