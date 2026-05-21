import random
import string
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class Participant(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    joined_at: datetime = Field(default_factory=datetime.now)


class SessionCreate(BaseModel):
    topic: str
    framework: str = "swot"
    custom_categories: list[str] = []


class Session(SessionCreate):
    id: str = Field(default_factory=lambda: uuid4().hex)
    access_code: str = ""
    status: str = "active"
    participants: list[Participant] = []
    created_at: datetime = Field(default_factory=datetime.now)


class JoinResponse(BaseModel):
    participant_id: str


class JoinByCodeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def generate_access_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))
