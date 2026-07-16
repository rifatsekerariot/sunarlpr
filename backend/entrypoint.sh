#!/bin/sh
set -e

echo "Waiting for postgres to be ready..."
sleep 5

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -m app.seed || echo "Seed already applied or skipped."

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
