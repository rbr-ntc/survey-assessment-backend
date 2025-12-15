#!/usr/bin/env sh
set -eu

echo "[start] booting backend..."

# Derive POSTGRES_URL from Railway DATABASE_URL if needed.
if [ -z "${POSTGRES_URL:-}" ] && [ -n "${DATABASE_URL:-}" ]; then
  POSTGRES_URL="$(echo "$DATABASE_URL" | sed 's|^postgresql://|postgresql+asyncpg://|; s|^postgres://|postgresql+asyncpg://|')"
  export POSTGRES_URL
  echo "[start] derived POSTGRES_URL from DATABASE_URL"
fi

# Run migrations on container start (idempotent).
if [ -n "${POSTGRES_URL:-}" ]; then
  echo "[start] running alembic migrations..."
  i=1
  while [ "$i" -le 20 ]; do
    if alembic upgrade head; then
      echo "[start] migrations done"
      break
    fi
    echo "[start] migration attempt $i failed; retrying in 2s..."
    i=$((i+1))
    sleep 2
  done
else
  echo "[start] POSTGRES_URL/DATABASE_URL not set; skipping migrations"
fi

# Run MongoDB quiz_content migration (idempotent - checks if document exists)
if [ -n "${MONGO_URL:-}" ] && [ -f "scripts/migrate_quiz_content.py" ]; then
  echo "[start] running MongoDB quiz_content migration..."
  python scripts/migrate_quiz_content.py || echo "[start] MongoDB migration failed or already done (this is OK)"
else
  echo "[start] MONGO_URL not set or migration script not found; skipping MongoDB migration"
fi

echo "[start] starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
