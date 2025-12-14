#!/bin/bash
# Script to run Alembic migrations on Railway
# Usage: railway run bash railway_migrations.sh

set -e

echo "🚀 Starting database migrations..."

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if POSTGRES_URL is set
if [ -z "$POSTGRES_URL" ] && [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: POSTGRES_URL or DATABASE_URL not set"
    exit 1
fi

# Convert DATABASE_URL to POSTGRES_URL if needed
if [ -z "$POSTGRES_URL" ] && [ -n "$DATABASE_URL" ]; then
    export POSTGRES_URL=$(echo $DATABASE_URL | sed 's|postgresql://|postgresql+asyncpg://|' | sed 's|postgres://|postgresql+asyncpg://|')
    echo "✅ Converted DATABASE_URL to POSTGRES_URL"
fi

echo "📊 Running migrations..."
alembic upgrade head

echo "✅ Migrations completed successfully!"

