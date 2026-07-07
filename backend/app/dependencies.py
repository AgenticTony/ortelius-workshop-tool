from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session as DBSession

from app.database import SessionLocal
from app.errors import AuthenticationError, SessionNotFoundError
from app.models.db_models import ParticipantDB, SessionDB
from app.security import verify_token
from app.services.event_bus import EventBusProtocol, event_bus


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_event_bus() -> EventBusProtocol:
    """FastAPI DI seam for the event bus.

    Returns the process-wide in-memory singleton. Routes depend on this
    Protocol, not the concrete class, so a future shared broker (Redis pub/sub
    or Postgres LISTEN/NOTIFY for multi-worker) can be wired in at this single
    composition point. Override via ``app.dependency_overrides`` in tests.
    """
    return event_bus


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


@dataclass
class Principal:
    """The authenticated caller for a participant-scoped route.

    Either the session's facilitator (``role="facilitator"``, who can act on
    any participant route in their session) or a joined participant
    (``role="participant"`` with ``participant_id`` set).
    """

    role: str
    session_id: str
    participant_id: str | None = None


def resolve_principal(session_id: str, token: str | None, db: DBSession) -> Principal:
    """Validate a token as facilitator-or-participant for the session.

    Shared by the header-based dependency and the SSE endpoint (which can't
    send headers via EventSource, so it passes the token as a query param).
    """
    if not token:
        raise AuthenticationError("Bearer token required")
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)
    if verify_token(token, session.facilitator_token_hash):
        return Principal(role="facilitator", session_id=session_id)
    # A session can have many participants; check each stored hash.
    participant = (
        db.query(ParticipantDB)
        .filter(ParticipantDB.session_id == session_id)
        .all()
    )
    for p in participant:
        if p.token_hash and verify_token(token, p.token_hash):
            return Principal(role="participant", session_id=session_id, participant_id=p.id)
    raise AuthenticationError("Invalid or expired token")


def get_principal(
    session_id: str,
    authorization: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
) -> Principal:
    """Authorize a participant-or-facilitator caller via the Authorization header."""
    return resolve_principal(session_id, _extract_bearer(authorization), db)
