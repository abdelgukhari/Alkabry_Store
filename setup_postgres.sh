#!/bin/bash
# PostgreSQL Setup Script for AlKabry Ecommerce
# Run this script once to create the database and user

set -e

echo "======================================"
echo "PostgreSQL Setup for AlKabry Ecommerce"
echo "======================================"
echo ""

# Configuration
DB_NAME="ecommerce_alkabry"
DB_USER="ecommerce_user"
DB_PASSWORD="ecommerce_pass_2026"
DB_HOST="localhost"
DB_PORT="5432"

echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Password: $DB_PASSWORD"
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo ""

# Run PostgreSQL commands
sudo -u postgres psql <<EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
        RAISE NOTICE 'User $DB_USER created.';
    ELSE
        RAISE NOTICE 'User $DB_USER already exists.';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to the database and grant schema privileges
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

EOF

echo ""
echo "======================================"
echo "✓ PostgreSQL setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. pip install psycopg2-binary"
echo "2. Update config/settings.py DATABASES"
echo "3. python manage.py migrate"
echo "4. python manage.py seed_data"
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
