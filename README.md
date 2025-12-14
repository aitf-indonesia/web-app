# PRD Analyst

Pengawasan Ruang Digital (PRD) Analyst is a monitoring system designed to detect, verify, and block online-gambling content across websites, social media, and public reports using AI-powered classification with human-in-the-loop validation.

## Documentation

**[Docker Setup](DOCKER.md)** - Docker-based deployment guide with docker-compose

**[Quick Start Guide](DOCKER-QUICKSTART.md)** - Quick reference for common Docker commands

## Quick Start

### Docker Deployment (Recommended)

```bash
# Start all services with Docker
./docker-dev.sh start

# Access at http://localhost
```

See [DOCKER.md](DOCKER.md) for complete Docker setup instructions.

### Manual Deployment

For VPS/RunPod deployment without Docker, see archived guides in `archives/vps-deployment/GUIDES.md`.

## Architecture

```
Docker Container
    ↓
Nginx (Port 80) - Reverse Proxy
    ├─ /api/ → Backend (Port 8000) - FastAPI
    └─ /     → Frontend (Port 3000) - Next.js
    ↓
PostgreSQL (Port 5432) - Database
```

## Project Structure

```
prototype-dashboard-chatbot/
├── frontend/              # Next.js application
├── backend/               # FastAPI application
├── database/              # Database initialization scripts
├── archives/              # Archived legacy files
├── docker-compose.yml     # Docker orchestration
├── nginx.docker.conf      # Nginx configuration for Docker
├── docker-dev.sh          # Docker helper script
├── DOCKER.md              # Docker documentation
└── README.md              # This file
```

## Tech Stack

### Frontend
- **Next.js** 16.0.0 - React framework
- **React** 19.2.0 - UI library
- **TailwindCSS** 4 - Styling framework
- **TypeScript** - Type-safe JavaScript
- **Radix UI** - Accessible component primitives
- **Recharts** - Data visualization
- **React Markdown** - Markdown rendering

### Backend
- **FastAPI** - Modern Python web framework
- **Python** 3.11 - Programming language
- **Uvicorn** - ASGI server
- **PostgreSQL** 14 - Relational database
- **SQLAlchemy** - ORM (if used)
- **Pydantic** - Data validation
- **Google Gemini API** - AI/LLM integration

### Infrastructure & DevOps
- **PM2** - Process manager for Node.js and Python
- **Nginx** - Reverse proxy server
- **RunPod** - Container hosting platform
- **Conda** - Python environment manager (prd6)
- **nvm** - Node.js version manager

### Development Tools
- **pnpm** - Fast package manager
- **Chrome** - Web browser for testing
- **ChromeDriver** - Browser automation
- **Selenium** (if used) - Web scraping/automation

### Database & Storage
- **PostgreSQL** 14 - Primary database
- Local file storage for screenshots and assets

**Last Updated**: 2025-12-01  
**Team**: PRD Analyst Team - AITF Universitas Brawijaya 2025
