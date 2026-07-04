"""Alembic migration environment for the Workshop Tool.

Targets the app's SQLAlchemy ``Base.metadata`` and resolves the DB URL from
``app.config.settings`` (or a ``DATABASE_URL`` env var) so the same config
works for docker-compose, local ``.env``, and Supabase — nothing is hardcoded
in alembic.ini.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make ``app`` importable when alembic runs from the backend/ dir (where
# alembic.ini lives). alembic is invoked as ``alembic upgrade head`` from
# backend/, so cwd is already backend/ — but be defensive for IDE runs.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Import the app's Base + models so target_metadata is fully populated.
from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.models import db_models  # noqa: F401,E402  (registers models on Base)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The single source of truth for autogenerate.
target_metadata = Base.metadata


def _resolve_url() -> str:
    """Resolve the DB URL from the app settings, falling back to env var."""
    url = settings.database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "No DATABASE_URL configured. Set it in backend/.env or the "
            "DATABASE_URL environment variable before running alembic."
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL without a live connection)."""
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = engine_from_config(
        {"sqlalchemy.url": _resolve_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
