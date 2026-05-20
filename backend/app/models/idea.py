from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class IdeaCreate(BaseModel):
    """Request body for submitting an idea."""
    participant_id: str
    content: str


class Idea(IdeaCreate):
    """Full idea object returned in responses."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    votes: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
