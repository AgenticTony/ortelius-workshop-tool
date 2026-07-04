from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.dependencies import get_db
from app.errors import (
    AccessCodeCollisionError,
    InvalidAccessCodeError,
    SessionNotFoundError,
)
from app.models import JoinByCodeRequest, JoinResponse, Participant, Session, SessionCreate
from app.models.db_models import ParticipantDB, SessionDB
from app.models.session import generate_access_code
from app.security import generate_facilitator_token, hash_token
from app.services.event_bus import EVENT_PARTICIPANT_JOINED, event_bus

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=Session)
def create_session(body: SessionCreate, db: DBSession = Depends(get_db)):
    code = _unique_access_code(db)
    # Issue a facilitator token. Store the hash, return the plaintext once.
    token = generate_facilitator_token()
    db_session = SessionDB(
        **body.model_dump(),
        access_code=code,
        facilitator_token_hash=hash_token(token),
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    session = _to_session(db_session)
    session.facilitator_token = token
    return session


@router.post("/join/{access_code}", response_model=JoinResponse)
def join_by_code(access_code: str, body: JoinByCodeRequest, db: DBSession = Depends(get_db)):
    db_session = db.query(SessionDB).filter(SessionDB.access_code == access_code).first()
    if not db_session:
        raise InvalidAccessCodeError()
    participant = ParticipantDB(session_id=db_session.id, name=body.name.strip())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    _publish_participant_joined(db_session.id, participant, db)
    return JoinResponse(participant_id=participant.id, session_id=db_session.id)


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    db_session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not db_session:
        raise SessionNotFoundError(session_id)
    return _to_session(db_session)


@router.post("/{session_id}/join", response_model=JoinResponse)
def join_session(session_id: str, name: str = "", db: DBSession = Depends(get_db)):
    if not name.strip():
        # Input validation — keep as HTTPException for FastAPI's native 422 shape.
        raise HTTPException(status_code=422, detail="Name is required")
    db_session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not db_session:
        raise SessionNotFoundError(session_id)
    participant = ParticipantDB(session_id=session_id, name=name.strip())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    _publish_participant_joined(session_id, participant, db)
    return JoinResponse(participant_id=participant.id, session_id=session_id)


def _unique_access_code(db: DBSession, max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        code = generate_access_code()
        if not db.query(SessionDB).filter(SessionDB.access_code == code).first():
            return code
    raise AccessCodeCollisionError()


def _to_session(db_session: SessionDB) -> Session:
    return Session(
        id=db_session.id,
        topic=db_session.topic,
        framework=db_session.framework,
        custom_categories=db_session.custom_categories or [],
        access_code=db_session.access_code,
        status=db_session.status,
        participants=[Participant(id=p.id, name=p.name, joined_at=p.joined_at) for p in db_session.participants],
        created_at=db_session.created_at,
        # facilitator_token intentionally omitted: only set on the create response.
    )


def _publish_participant_joined(session_id: str, participant: ParticipantDB, db: DBSession) -> None:
    """Broadcast a participant_joined SSE event with the new participant count."""
    count = db.query(ParticipantDB).filter(ParticipantDB.session_id == session_id).count()
    event_bus.publish(session_id, EVENT_PARTICIPANT_JOINED, {
        "participant_id": participant.id,
        "name": participant.name,
        "participant_count": count,
    })
