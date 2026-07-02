from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Timezone-aware UTC now. Keeps API responses consistent with DB models."""
    return datetime.now(timezone.utc)


class IdeaCreate(BaseModel):
    participant_id: str
    participant_name: str = Field(default="", min_length=0, max_length=100)
    content: str = Field(min_length=1, max_length=2000)
    category: str | None = None


class Idea(IdeaCreate):
    id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    votes: int = 0
    created_at: datetime = Field(default_factory=_utcnow)
