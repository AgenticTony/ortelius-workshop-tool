from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession

from app.dependencies import get_db
from app.models import SessionCreate, Session, Participant, JoinResponse, JoinByCodeRequest
from app.models.session import generate_access_code
from app.models.db_models import SessionDB, ParticipantDB

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=Session)
def create_session(body: SessionCreate, db: DBSession = Depends(get_db)):
    code = _unique_access_code(db)
    db_session = SessionDB(**body.model_dump(), access_code=code)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return _to_session(db_session)


@router.post("/join/{access_code}", response_model=JoinResponse)
def join_by_code(access_code: str, body: JoinByCodeRequest, db: DBSession = Depends(get_db)):
    db_session = db.query(SessionDB).filter(SessionDB.access_code == access_code).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Invalid access code")
    participant = ParticipantDB(session_id=db_session.id, name=body.name.strip())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return JoinResponse(participant_id=participant.id)


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    db_session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_session(db_session)


@router.post("/{session_id}/join", response_model=JoinResponse)
def join_session(session_id: str, name: str = "", db: DBSession = Depends(get_db)):
    if not name.strip():
        raise HTTPException(status_code=422, detail="Name is required")
    db_session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    participant = ParticipantDB(session_id=session_id, name=name.strip())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return JoinResponse(participant_id=participant.id)


def _unique_access_code(db: DBSession, max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        code = generate_access_code()
        if not db.query(SessionDB).filter(SessionDB.access_code == code).first():
            return code
    raise RuntimeError("Could not generate a unique access code")


def _to_session(db_session: SessionDB) -> Session:
    return Session(
        id=db_session.id,
        topic=db_session.topic,
        framework=db_session.framework,
        custom_categories=db_session.custom_categories or [],
        access_code=db_session.access_code,
        status=db_session.status,
        participants=[Participant(id=p.id, name=p.name) for p in db_session.participants],
        created_at=db_session.created_at,
    )
