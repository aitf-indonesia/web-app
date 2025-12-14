# Database Initialization Files

This directory contains SQL files for initializing the PRD Analyst database in Docker.

## Files

### 1. `init-schema.sql` (14KB)
Database schema definition including:
- **Tables**: 11 tables (users, results, generated_domains, audit_log, etc.)
- **Sequences**: Auto-increment sequences for primary keys
- **Constraints**: Primary keys, foreign keys, check constraints
- **Defaults**: Default values and timestamps

**Tables**:
- `users` - User accounts and authentication
- `results` - Analysis results and verification status
- `generated_domains` - Generated domain list
- `audit_log` - Audit trail for all actions
- `chat_history` - Chat conversations per domain
- `domain_notes` - Notes attached to domains
- `feedback` - User feedback
- `generator_settings` - Generator configuration
- `history_log` - Historical logs
- `object_detection` - Object detection results
- `reasoning` - AI reasoning results

### 2. `init-data.sql` (273KB)
Initial data for the database including:
- Sample users (admin, verif1, verif2, verif3, aliy)
- Generated domains with analysis results
- Audit log entries
- Chat history
- Domain notes

### 3. `init-db.sh`
Initialization script that:
1. Checks if database is already initialized
2. Creates schema from `init-schema.sql`
3. Loads data from `init-data.sql` (optional)
4. Falls back to `backup/prd_backup.sql` if data file not found

## Usage

### Automatic Initialization (Docker)

When you start the PostgreSQL container for the first time, the initialization happens automatically:

```bash
docker-compose up -d postgres
```

The script will:
1. Create all tables and sequences
2. Load initial data
3. Set up constraints and indexes

### Manual Initialization

If you need to manually initialize the database:

```bash
# Schema only
psql -U postgres -d prd < database/init-schema.sql

# Schema + Data
psql -U postgres -d prd < database/init-schema.sql
psql -U postgres -d prd < database/init-data.sql
```

### Fresh Start

To reset the database and reinitialize:

```bash
# Stop and remove containers with volumes
docker-compose down -v

# Start again (will reinitialize)
docker-compose up -d
```

## Schema Overview

### Core Tables

**Users & Authentication**
- `users` - User accounts with roles (administrator, verifikator)

**Domain Analysis**
- `generated_domains` - List of generated/crawled domains
- `results` - Final analysis results with verification status
- `reasoning` - AI reasoning for each domain
- `object_detection` - Object detection results

**Collaboration**
- `chat_history` - Chat messages per domain
- `domain_notes` - Notes attached to domains
- `feedback` - User feedback

**Audit & History**
- `audit_log` - Complete audit trail
- `history_log` - Historical activity logs

**Configuration**
- `generator_settings` - Generator keywords and settings

## Maintenance

### Updating Schema

If you need to update the schema:

1. Make changes to the database
2. Export new schema:
   ```bash
   docker-compose exec postgres pg_dump -U postgres -d prd --schema-only > database/init-schema.sql
   ```

### Updating Data

To update the initial data:

1. Make changes to the database
2. Export data only:
   ```bash
   docker-compose exec postgres pg_dump -U postgres -d prd --data-only > database/init-data.sql
   ```

### Full Backup

To create a complete backup:

```bash
docker-compose exec postgres pg_dump -U postgres -d prd > archives/backup/prd_backup_$(date +%Y%m%d).sql
```

## Notes

- Schema and data are separated for easier maintenance
- Schema file is version-controlled
- Data file contains sample/seed data
- Old backups are stored in `archives/backup/` folder
- All files use PostgreSQL 14 format

---

**Last Updated**: 2025-12-14  
**Database Version**: PostgreSQL 14
