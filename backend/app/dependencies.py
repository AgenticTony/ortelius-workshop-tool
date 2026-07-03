from fastapi import Depends, Header
from sqlalchemy.orm import Session as DBSession

from app.database import SessionLocal
from app.errors import AuthenticationError, SessionNotFoundError
from app.models.db_models import SessionDB
from app.security import verify_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_bearer(authorization: str | None) -> str:
    """Pull the token out of an 'Authorization: Bearer <token>' header."""
    if not authorization:
        raise AuthenticationError("Authorization header required")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise AuthenticationError("Invalid authorization header. Expected 'Bearer <token>'")
    return parts[1].strip()


def get_facilitator(
    session_id: str,
    authorization: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
) -> SessionDB:
    """Resolve and authorize the facilitator for a session.

    Validates the bearer token against the stored hash. Used to gate
    cost-incurring or privileged routes (analysis, report).

    Returns the authorized SessionDB row so the route also gets its session.
    """
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    # Same not-found message as other routes so we don't leak session existence.
    if not session:
        raise SessionNotFoundError(session_id)

    token = _extract_bearer(authorization)
    if not verify_token(token, session.facilitator_token_hash):
        raise AuthenticationError("Invalid or expired facilitator token")
    return session
