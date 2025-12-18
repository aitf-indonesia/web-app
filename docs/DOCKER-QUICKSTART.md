# Docker Quick Reference - PRD Analyst

## 🚀 Quick Start

```bash
# Start everything
./docker-dev.sh start

# Access at http://localhost
```

## 📋 Common Commands

```bash
# Service Management
./docker-dev.sh start          # Start all services
./docker-dev.sh stop           # Stop all services
./docker-dev.sh restart        # Restart all services
./docker-dev.sh status         # Check service status

# Logs & Debugging
./docker-dev.sh logs           # View all logs
./docker-dev.sh logs backend   # View backend logs
./docker-dev.sh logs frontend  # View frontend logs
./docker-dev.sh logs postgres  # View database logs

# Database
./docker-dev.sh db-backup      # Backup database
./docker-dev.sh db-restore backup/prd_backup.sql  # Restore

# Development
./docker-dev.sh shell backend  # Open backend shell
./docker-dev.sh shell frontend # Open frontend shell
./docker-dev.sh build          # Rebuild all images
./docker-dev.sh clean          # Remove everything
```

## 🌐 Service URLs

- **Application**: http://localhost
- **Backend API**: http://localhost/api
- **Database**: localhost:5432

## 📁 Important Files

- `docker-compose.yml` - Service orchestration
- `.env.docker` - Environment variables
- `nginx.docker.conf` - Nginx configuration
- `DOCKER.md` - Complete documentation

## 🔧 Troubleshooting

```bash
# Check service status
docker-compose ps

# View logs
./docker-dev.sh logs

# Restart specific service
docker-compose restart backend

# Clean restart
./docker-dev.sh clean
./docker-dev.sh start
```

## 📦 What's Included

- ✅ Frontend (Next.js) - Port 3000
- ✅ Backend (FastAPI) - Port 8000
- ✅ Database (PostgreSQL 14) - Port 5432
- ✅ Nginx Reverse Proxy - Port 80/443
- ✅ Auto database restore from backup
- ✅ Health checks for all services
- ✅ Persistent volumes for data
- ✅ Development hot-reload support

## 📖 Full Documentation

See [DOCKER.md](DOCKER.md) for complete setup and usage guide.
