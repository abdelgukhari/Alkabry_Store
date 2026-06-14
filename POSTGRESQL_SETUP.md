# PostgreSQL Setup Guide

This guide will help you migrate from SQLite to PostgreSQL for better performance and production readiness.

---

## Prerequisites

- PostgreSQL 14+ installed (already installed: v18.1)
- PostgreSQL service running
- sudo access

---

## Option 1: Quick Setup (Recommended)

### Step 1: Run the Setup Script

```bash
chmod +x setup_postgres.sh
./setup_postgres.sh
```

This script will:
- Create database user: `ecommerce_user`
- Create database: `ecommerce_alkabry`
- Set up proper permissions

### Step 2: Install PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

### Step 3: Configure Django

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and set:

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_alkabry
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass_2026
DB_HOST=localhost
DB_PORT=5432
```

### Step 4: Run Migrations

```bash
python manage.py migrate
```

### Step 5: Generate Benchmark Data

```bash
python manage.py generate_benchmark_data
```

---

## Option 2: Manual Setup

### Step 1: Create PostgreSQL User and Database

```bash
# Open PostgreSQL shell
sudo -u postgres psql

# Run these SQL commands:
CREATE USER ecommerce_user WITH PASSWORD 'ecommerce_pass_2026';
CREATE DATABASE ecommerce_alkabry OWNER ecommerce_user;
GRANT ALL PRIVILEGES ON DATABASE ecommerce_alkabry TO ecommerce_user;

# Connect to the database
\c ecommerce_alkabry

# Grant schema permissions
GRANT ALL ON SCHEMA public TO ecommerce_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ecommerce_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ecommerce_user;

# Exit
\q
```

### Step 2: Install PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

### Step 3: Configure Django

Create `.env` file:

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_alkabry
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass_2026
DB_HOST=localhost
DB_PORT=5432
```

### Step 4: Migrate and Generate Data

```bash
python manage.py migrate
python manage.py generate_benchmark_data
python manage.py runserver
```

---

## Verify Connection

```bash
# Test PostgreSQL connection
psql -h localhost -U ecommerce_user -d ecommerce_alkabry

# Or test Django connection
python manage.py dbshell
```

---

## Database Configuration Reference

### Switching Between SQLite and PostgreSQL

**Use SQLite (Development):**
```env
DB_ENGINE=sqlite
```

**Use PostgreSQL (Production):**
```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_alkabry
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass_2026
DB_HOST=localhost
DB_PORT=5432
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_ENGINE` | Database engine (`sqlite` or `postgresql`) | `sqlite` |
| `DB_NAME` | Database name | `ecommerce_alkabry` |
| `DB_USER` | Database user | `ecommerce_user` |
| `DB_PASSWORD` | Database password | `ecommerce_pass_2026` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

---

## Migrate Data from SQLite to PostgreSQL

If you already have data in SQLite and want to migrate:

### Step 1: Export SQLite Data

```bash
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > backup.json
```

### Step 2: Setup PostgreSQL

Follow Option 1 or 2 above to setup PostgreSQL.

### Step 3: Import to PostgreSQL

```bash
# Ensure DB_ENGINE=postgresql in .env
python manage.py migrate
python manage.py loaddata backup.json
```

---

## PostgreSQL Maintenance

### Backup Database

```bash
pg_dump -h localhost -U ecommerce_user ecommerce_alkabry > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
psql -h localhost -U ecommerce_user ecommerce_alkabry < backup_20260404.sql
```

### Check Database Size

```bash
psql -h localhost -U ecommerce_user -d ecommerce_alkabry -c "SELECT pg_size_pretty(pg_database_size('ecommerce_alkabry'));"
```

### View Tables and Sizes

```bash
psql -h localhost -U ecommerce_user -d ecommerce_alkabry -c "
SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS total_size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;
"
```

---

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Authentication Failed

```bash
# Check pg_hba.conf
sudo nano /etc/postgresql/18/main/pg_hba.conf

# Ensure this line exists:
local   all   all   md5
host    all   all   127.0.0.1/32   md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Permission Denied

```bash
# Grant all permissions
sudo -u postgres psql -d ecommerce_alkabry -c "GRANT ALL ON SCHEMA public TO ecommerce_user;"
```

---

## Production Deployment

For production, use these recommended settings:

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_alkabry_prod
DB_USER=ecommerce_prod_user
DB_PASSWORD=<strong-random-password>
DB_HOST=<production-db-host>
DB_PORT=5432
```

### Production PostgreSQL Configuration

In `config/settings.py`, adjust:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require',  # For cloud databases
        },
    }
}
```

---

## Quick Commands Reference

| Task | Command |
|------|---------|
| Start PostgreSQL | `sudo systemctl start postgresql` |
| Stop PostgreSQL | `sudo systemctl stop postgresql` |
| Check Status | `pg_isready` |
| Open psql Shell | `psql -h localhost -U ecommerce_user -d ecommerce_alkabry` |
| Backup | `pg_dump -h localhost -U ecommerce_user ecommerce_alkabry > backup.sql` |
| Restore | `psql -h localhost -U ecommerce_user ecommerce_alkabry < backup.sql` |
| Django Migrate | `python manage.py migrate` |
| Django Shell | `python manage.py dbshell` |

---

**Ready to use! Just run `./setup_postgres.sh` and follow the steps.**
