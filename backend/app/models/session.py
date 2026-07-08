import secrets
import string
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.frameworks import build_custom_framework, get_framework


def _utcnow() -> datetime:
    """Timezone-aware UTC now. Keeps API responses consistent with DB models."""
    return datetime.now(timezone.utc)


class Participant(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    joined_at: datetime = Field(default_factory=_utcnow)


class SessionCreate(BaseModel):
    topic: str
    framework: str = "swot"
    custom_categories: list[str] = []
    # Dot-voting: max votes each participant may cast across the session.
    # No create-session UI exposes this yet — default 3 (classic dot-voting).
    vote_budget: int = 3

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
    created_at: datetime = Field(default_factory=_utcnow)
    # Plaintext facilitator token. Only populated on the create-session
    # response so the facilitator can store it; never persisted or re-served.
    facilitator_token: str | None = None


class JoinResponse(BaseModel):
    participant_id: str
    # session_id is included so a client that joined by access code (where it
    # doesn't otherwise know the session id) can fetch session details and
    # subscribe to the SSE stream. Additive, non-breaking.
    session_id: str | None = None
    # Participant bearer token (issued once at join). Required to submit ideas,
    # vote, and open the SSE stream. Only set on the join response — never
    # persisted in plaintext (we store its hash) or re-served.
    participant_token: str | None = None


class JoinByCodeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class JoinRequest(BaseModel):
    """Body for POST /sessions/{id}/join (the session-id join path).

    The name travels in the JSON body — not the query string — so it never
    lands in access logs, browser history, or referrer headers. (This path
    used to send ``?name=`` which is a PII hygiene leak; the access-code join
    already used a body.)
    """

    name: str = Field(min_length=1, max_length=100)


def generate_access_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    # secrets.choice (CSPRNG) rather than random.choices (Mersenne Twister) —
    # access codes are a join credential, so use a cryptographically secure RNG.
    return "".join(secrets.choice(chars) for _ in range(length))
