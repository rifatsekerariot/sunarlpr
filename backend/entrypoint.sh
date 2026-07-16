#!/bin/sh
# Wait for PostgreSQL to be ready
echo "Waiting for postgres..."
sleep 3

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -c "import sys; sys.path.append('/app'); import app.seed"

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
