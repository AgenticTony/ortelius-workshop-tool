#!/bin/sh
# Container entrypoint: ensure the schema exists, then launch the API.
# Safe to run on every restart — init_db is idempotent.
set -e

echo "Ensuring database schema exists..."
python -m app.init_db

echo "Starting uvicorn on 0.0.0.0:8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
