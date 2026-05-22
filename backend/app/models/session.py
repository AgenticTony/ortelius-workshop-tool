import random
import string
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.frameworks import get_framework, build_custom_framework


class Participant(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    joined_at: datetime = Field(default_factory=datetime.now)


class SessionCreate(BaseModel):
    topic: str
    framework: str = "swot"
    custom_categories: list[str] = []

    @model_validator(mode="after")
    def validate_framework(self) -> "SessionCreate":
        if self.framework == "custom":
            build_custom_framework(self.custom_categories)
            return self

        try:
            get_framework(self.framework)
        except ValueError as e:
            raise ValueError(str(e)) from e

        if self.custom_categories:
            self.custom_categories = []
        return self


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
