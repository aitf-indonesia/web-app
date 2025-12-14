#!/bin/bash
# Docker Development Helper Script
# Usage: ./docker-dev.sh [command]

set -e

COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.docker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Commands
cmd_start() {
    print_info "Starting all services..."
    docker-compose --env-file $ENV_FILE up -d
    print_success "All services started!"
    echo ""
    print_info "Access the application at: http://localhost"
    print_info "Backend API at: http://localhost/api"
    echo ""
    cmd_status
}

cmd_stop() {
    print_info "Stopping all services..."
    docker-compose down
    print_success "All services stopped!"
}

cmd_restart() {
    print_info "Restarting all services..."
    docker-compose restart
    print_success "All services restarted!"
}

cmd_build() {
    print_info "Building all images..."
    docker-compose build --no-cache
    print_success "All images built!"
}

cmd_logs() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f $SERVICE
    fi
}

cmd_status() {
    print_info "Service Status:"
    docker-compose ps
}

cmd_shell() {
    SERVICE=${1:-backend}
    print_info "Opening shell in $SERVICE container..."
    docker-compose exec $SERVICE /bin/sh
}

cmd_db_backup() {
    BACKUP_FILE="backup/prd_backup_$(date +%Y%m%d_%H%M%S).sql"
    print_info "Backing up database to $BACKUP_FILE..."
    docker-compose exec -T postgres pg_dump -U postgres prd > $BACKUP_FILE
    print_success "Database backed up to $BACKUP_FILE"
}

cmd_db_restore() {
    BACKUP_FILE=${1:-backup/prd_backup.sql}
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    print_info "Restoring database from $BACKUP_FILE..."
    docker-compose exec -T postgres psql -U postgres prd < $BACKUP_FILE
    print_success "Database restored from $BACKUP_FILE"
}

cmd_clean() {
    print_info "Cleaning up containers, volumes, and images..."
    docker-compose down -v
    print_success "Cleanup complete!"
}

cmd_help() {
    cat << EOF
Docker Development Helper Script

Usage: ./docker-dev.sh [command] [options]

Commands:
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    build           Build all images (no cache)
    logs [service]  View logs (all services or specific service)
    status          Show service status
    shell [service] Open shell in container (default: backend)
    db-backup       Backup database to backup/ directory
    db-restore [file] Restore database from backup file
    clean           Stop and remove all containers and volumes
    help            Show this help message

Examples:
    ./docker-dev.sh start
    ./docker-dev.sh logs backend
    ./docker-dev.sh shell frontend
    ./docker-dev.sh db-backup
    ./docker-dev.sh db-restore backup/prd_backup.sql

EOF
}

# Main command dispatcher
COMMAND=${1:-help}

case $COMMAND in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    build)
        cmd_build
        ;;
    logs)
        cmd_logs $2
        ;;
    status)
        cmd_status
        ;;
    shell)
        cmd_shell $2
        ;;
    db-backup)
        cmd_db_backup
        ;;
    db-restore)
        cmd_db_restore $2
        ;;
    clean)
        cmd_clean
        ;;
    help|*)
        cmd_help
        ;;
esac
