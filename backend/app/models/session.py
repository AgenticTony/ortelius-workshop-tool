from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Participant(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str


class SessionCreate(BaseModel):
    """Request body for creating a session."""
    topic: str
    framework: str = "swot"
    custom_categories: list[str] = []


class Session(SessionCreate):
    """Full session object returned in responses."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    status: str = "active"
    participants: list[Participant] = []
    created_at: datetime = Field(default_factory=datetime.now)
