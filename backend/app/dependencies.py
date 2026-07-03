from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.database import SessionLocal
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
        raise HTTPException(status_code=404, detail="Session not found")

    token = _extract_bearer(authorization)
    if not verify_token(token, session.facilitator_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired facilitator token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session
