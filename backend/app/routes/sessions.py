from fastapi import APIRouter, HTTPException

from app.models import SessionCreate, Session, Participant

router = APIRouter(prefix="/sessions", tags=["sessions"])

sessions: dict[str, Session] = {}


@router.post("", response_model=Session)
def create_session(body: SessionCreate):
    session = Session(**body.model_dump())
    sessions[session.id] = session
    return session


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@router.post("/{session_id}/join", response_model=Session)
def join_session(session_id: str, name: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    participant = Participant(name=name)
    sessions[session_id].participants.append(participant)
    return sessions[session_id]
