from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models import SessionCreate, Session, Participant
from app.models.db_models import SessionDB, ParticipantDB
from app.database import SessionLocal

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=Session)
def create_session(body: SessionCreate, db: Session = Depends(get_db)):
    db_session = SessionDB(**body.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return Session(
        id=db_session.id,
        topic=db_session.topic,
        framework=db_session.framework,
        custom_categories=db_session.custom_categories or [],
        status=db_session.status,
        participants=[],
        created_at=db_session.created_at,
    )


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return Session(
        id=db_session.id,
        topic=db_session.topic,
        framework=db_session.framework,
        custom_categories=db_session.custom_categories or [],
        status=db_session.status,
        participants=[
            Participant(id=p.id, name=p.name) for p in db_session.participants
        ],
        created_at=db_session.created_at,
    )


@router.post("/{session_id}/join", response_model=Session)
def join_session(session_id: str, name: str, db: Session = Depends(get_db)):
    db_session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    participant = ParticipantDB(session_id=session_id, name=name)
    db.add(participant)
    db.commit()
    db.refresh(db_session)
    return Session(
        id=db_session.id,
        topic=db_session.topic,
        framework=db_session.framework,
        custom_categories=db_session.custom_categories or [],
        status=db_session.status,
        participants=[
            Participant(id=p.id, name=p.name) for p in db_session.participants
        ],
        created_at=db_session.created_at,
    )
