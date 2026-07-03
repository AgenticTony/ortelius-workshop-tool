#!/bin/sh
# Container entrypoint: apply migrations, then launch the API.
# `alembic upgrade head` is idempotent — safe on every restart. It creates the
# schema on a fresh DB and is a no-op on an already-migrated one.
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Starting uvicorn on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
