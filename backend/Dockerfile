# Workshop Tool API — backend image
#
# Matches the local dev runtime (Python 3.13). Uses -sllim for a small base.
# Build tooling (gcc, libpq-dev) is installed because psycopg2-binary may need
# to compile from source on some arch/Python combinations (e.g. arm64 + cp313);
# the binary wheel is used when available and the tooling is then inert.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps: build tooling for psycopg2 (fallback), curl for healthchecks.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so they cache independently of source changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application source.
COPY app/ ./app/

# Alembic migrations + config (entrypoint runs `alembic upgrade head`).
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 8000

# Entryppoint: ensure schema exists, then launch uvicorn bound to 0.0.0.0
# so the container is reachable from the host / other compose services.
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
