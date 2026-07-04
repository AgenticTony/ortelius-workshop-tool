from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _build_engine(url: str):
    """Create the SQLAlchemy engine with pool tuning appropriate to the backend.

    - SQLite (tests / local file): default pool (StaticPool is the caller's
      concern via connect_args; we don't impose QueuePool, which SQLite rejects).
    - Empty URL (dev without .env): create_engine("") yields an inert engine
      that's never actually used — pool config is irrelevant.
    - Postgres / Supabase (production): bounded QueuePool with pre-ping (so a
      recycled/dead connection after a managed-DB restart is detected and
      replaced instead of surfacing as a stale-connection error) and a recycle
      interval below typical managed-DB idle timeouts (e.g. Supabase's ~secs).
    """
    if not url or url.startswith("sqlite"):
        return create_engine(url)
    return create_engine(
        url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


engine = _build_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
