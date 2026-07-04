"""Create database tables for the Workshop Tool API.

Standalone schema bootstrap. Idempotent: SQLAlchemy ``create_all`` only
creates tables that don't already exist, so this is safe to run on every
container start.

This is the pragmatic bridge until Alembic migrations are introduced
(roadmap Step 15). Migrations will replace this file — they are the
proper tool for evolving a production schema.

Run with: ``python -m app.init_db``
"""

from app.database import Base, engine

# Importing db_models registers all ORM models with Base.metadata.
from app.models import db_models  # noqa: F401


def init_db() -> None:
    """Create all tables defined on Base.metadata if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("Database tables ensured.")


if __name__ == "__main__":
    init_db()
