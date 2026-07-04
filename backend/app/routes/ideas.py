import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session as DBSession

from app.dependencies import get_db
from app.errors import IdeaNotFoundError, SessionNotFoundError
from app.models import Idea, IdeaCreate
from app.models.db_models import IdeaDB, SessionDB
from app.rate_limit import limiter
from app.services.event_bus import EVENT_IDEA_ADDED, EVENT_IDEA_VOTED, event_bus

router = APIRouter(prefix="/sessions/{session_id}/ideas", tags=["ideas"])


@router.post("", response_model=Idea)
@limiter.limit("30/minute")
def submit_idea(request: Request, session_id: str, body: IdeaCreate, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)

    idea = IdeaDB(session_id=session_id, **body.model_dump())
    db.add(idea)
    db.commit()
    db.refresh(idea)

    # Notify live listeners (SSE) that a new idea landed.
    event_bus.publish(session_id, EVENT_IDEA_ADDED, _idea_to_dict(idea))
    return _to_idea(idea)


@router.get("", response_model=list[Idea])
def list_ideas(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)
    ideas = db.query(IdeaDB).filter(IdeaDB.session_id == session_id).all()
    return [_to_idea(idea) for idea in ideas]


@router.post("/{idea_id}/vote", response_model=Idea)
def vote_idea(session_id: str, idea_id: str, db: DBSession = Depends(get_db)):
    """Upvote an idea. v1 is a simple increment; per-participant dedup is future work."""
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise SessionNotFoundError(session_id)

    idea = (
        db.query(IdeaDB)
        .filter(IdeaDB.id == idea_id, IdeaDB.session_id == session_id)
        .first()
    )
    if not idea:
        raise IdeaNotFoundError(idea_id)

    idea.votes += 1
    db.commit()
    db.refresh(idea)

    event_bus.publish(session_id, EVENT_IDEA_VOTED, {"idea_id": idea.id, "votes": idea.votes})
    return _to_idea(idea)


def _to_idea(idea: IdeaDB) -> Idea:
    return Idea(
        id=idea.id,
        session_id=idea.session_id,
        participant_id=idea.participant_id,
        participant_name=idea.participant_name,
        category=idea.category,
        content=idea.content,
        votes=idea.votes,
        created_at=idea.created_at,
    )


def _idea_to_dict(idea: IdeaDB) -> dict:
    """Serialize an idea for SSE payloads (JSON-safe)."""
    return {
        "id": idea.id,
        "session_id": idea.session_id,
        "participant_id": idea.participant_id,
        "participant_name": idea.participant_name,
        "category": idea.category,
        "content": idea.content,
        "votes": idea.votes,
        "created_at": idea.created_at.isoformat() if idea.created_at else None,
    }


# Re-exported for the stream router so SSE payloads share one serializer.
idea_payload = _idea_to_dict


def _dumps_event(payload: dict) -> str:
    return json.dumps(payload, default=str)
