from fastapi import APIRouter, HTTPException

from app.models import IdeaCreate, Idea
from app.routes.sessions import sessions

router = APIRouter(prefix="/sessions/{session_id}/ideas", tags=["ideas"])

ideas: dict[str, list[Idea]] = {}


@router.post("", response_model=Idea)
def submit_idea(session_id: str, body: IdeaCreate):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    idea = Idea(session_id=session_id, **body.model_dump())

    if session_id not in ideas:
        ideas[session_id] = []
    ideas[session_id].append(idea)

    return idea


@router.get("", response_model=list[Idea])
def list_ideas(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return ideas.get(session_id, [])
