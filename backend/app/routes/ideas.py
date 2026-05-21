from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession

from app.dependencies import get_db
from app.models import IdeaCreate, Idea
from app.models.db_models import SessionDB, IdeaDB

router = APIRouter(prefix="/sessions/{session_id}/ideas", tags=["ideas"])


@router.post("", response_model=Idea)
def submit_idea(session_id: str, body: IdeaCreate, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    idea = IdeaDB(session_id=session_id, **body.model_dump())
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return _to_idea(idea)


@router.get("", response_model=list[Idea])
def list_ideas(session_id: str, db: DBSession = Depends(get_db)):
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    ideas = db.query(IdeaDB).filter(IdeaDB.session_id == session_id).all()
    return [_to_idea(idea) for idea in ideas]


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
