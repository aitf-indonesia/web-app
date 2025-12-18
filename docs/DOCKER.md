# Docker Setup Guide - PRD Analyst

Complete guide for running the PRD Analyst system using Docker.

## Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Requirements**: 
  - Minimum 4GB RAM
  - 10GB free disk space

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository (if not already done)
cd /home/aliy/Coding/prototype-dashboard-chatbot

# Copy environment file
cp .env.docker .env

# Make helper script executable
chmod +x docker-dev.sh
```

### 2. Start All Services

```bash
# Using helper script (recommended)
./docker-dev.sh start

# Or using docker-compose directly
docker-compose --env-file .env.docker up -d
```

### 3. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost/api
- **Database**: localhost:5432

Default credentials (if using backup):
- Check your existing user credentials from the backup

## Service Management

### Using Helper Script

The `docker-dev.sh` script provides convenient commands:

```bash
# Start all services
./docker-dev.sh start

# Stop all services
./docker-dev.sh stop

# Restart all services
./docker-dev.sh restart

# View logs (all services)
./docker-dev.sh logs

# View logs for specific service
./docker-dev.sh logs backend
./docker-dev.sh logs frontend
./docker-dev.sh logs postgres

# Check service status
./docker-dev.sh status

# Open shell in container
./docker-dev.sh shell backend
./docker-dev.sh shell frontend

# Backup database
./docker-dev.sh db-backup

# Restore database
./docker-dev.sh db-restore backup/prd_backup.sql

# Clean up (remove containers and volumes)
./docker-dev.sh clean
```

### Using Docker Compose Directly

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend

# Rebuild images
docker-compose build

# Remove everything including volumes
docker-compose down -v
```

## Environment Configuration

### Environment Variables

Edit `.env.docker` to configure the application:

```bash
# Database Configuration
DB_URL=postgresql://postgres:postgres@postgres:5432/prd
POSTGRES_DB=prd
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres  # Change in production!

# API Configuration
FRONTEND_URL=http://frontend:3000
NEXT_PUBLIC_API_URL=http://localhost/api

# Security
JWT_SECRET_KEY=your-secret-key-here  # Change in production!

# Environment
NODE_ENV=production
```

> [!WARNING]
> **Production Deployment**: Always change default passwords and secret keys before deploying to production!

## Database Management

### Automatic Initialization

On first startup, the database will automatically restore from `backup/prd_backup.sql` if it exists.

### Manual Backup

```bash
# Create backup
./docker-dev.sh db-backup

# Backup is saved to: backup/prd_backup_YYYYMMDD_HHMMSS.sql
```

### Manual Restore

```bash
# Restore from specific backup file
./docker-dev.sh db-restore backup/prd_backup.sql
```

### Direct Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d prd

# Run SQL commands
docker-compose exec postgres psql -U postgres -d prd -c "SELECT * FROM users;"
```

## Development Workflow

### Hot Reload

For development with hot reload:

1. **Backend**: The backend volume is mounted, so code changes will be reflected after restart:
   ```bash
   docker-compose restart backend
   ```

2. **Frontend**: For Next.js hot reload, you may want to run frontend locally:
   ```bash
   # Stop frontend container
   docker-compose stop frontend
   
   # Run frontend locally
   cd frontend
   npm run dev
   ```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Debugging

```bash
# Check service health
docker-compose ps

# Inspect container
docker inspect prd_backend

# Execute commands in container
docker-compose exec backend python --version
docker-compose exec frontend node --version

# Check network connectivity
docker-compose exec backend ping postgres
docker-compose exec frontend ping backend
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check if ports are already in use
sudo lsof -i :80
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :5432

# Clean up and restart
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

```bash
# Check if postgres is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Verify database is accessible
docker-compose exec postgres pg_isready -U postgres
```

### Frontend Build Issues

```bash
# Rebuild frontend image
docker-compose build --no-cache frontend

# Check frontend logs
docker-compose logs frontend
```

### Backend API Issues

```bash
# Check backend logs
docker-compose logs backend

# Verify backend can connect to database
docker-compose exec backend python -c "import db; print('DB OK')"

# Restart backend
docker-compose restart backend
```

### Nginx Issues

```bash
# Check nginx configuration
docker-compose exec nginx nginx -t

# Reload nginx
docker-compose exec nginx nginx -s reload

# Check nginx logs
docker-compose logs nginx
```

## Performance Optimization

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Volume Performance

For better performance on macOS/Windows, use named volumes instead of bind mounts for node_modules.

## Production Deployment

### Security Checklist

- [ ] Change default database password
- [ ] Change JWT secret key
- [ ] Use environment-specific `.env` file
- [ ] Enable HTTPS with SSL certificates
- [ ] Set up proper firewall rules
- [ ] Regular database backups
- [ ] Monitor container logs
- [ ] Set resource limits

### SSL/HTTPS Setup

Update `nginx.docker.conf` to include SSL configuration:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of configuration
}
```

Mount SSL certificates in docker-compose:

```yaml
nginx:
  volumes:
    - ./ssl:/etc/nginx/ssl:ro
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              Docker Host                     │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │  Nginx (Port 80/443)                   │ │
│  │  - Reverse Proxy                       │ │
│  └────────┬──────────────────┬────────────┘ │
│           │                  │               │
│  ┌────────▼────────┐  ┌─────▼──────────┐   │
│  │  Frontend       │  │  Backend       │   │
│  │  Next.js:3000   │  │  FastAPI:8000  │   │
│  └─────────────────┘  └────────┬───────┘   │
│                                 │            │
│                        ┌────────▼────────┐  │
│                        │  PostgreSQL     │  │
│                        │  Port 5432      │  │
│                        └─────────────────┘  │
│                                              │
│  Docker Network: prd_network                │
└─────────────────────────────────────────────┘
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Next.js Docker Documentation](https://nextjs.org/docs/deployment#docker-image)
- [FastAPI Docker Documentation](https://fastapi.tiangolo.com/deployment/docker/)

## Support

For issues or questions:
1. Check the logs: `./docker-dev.sh logs`
2. Review this documentation
3. Check Docker and Docker Compose versions
4. Ensure all prerequisites are met
