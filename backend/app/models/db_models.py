import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ParticipantDB(Base):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    # Indexed: token verification scans participants by session_id (O(log N)
    # lookup instead of a sequential scan per authed request).
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    # SHA-256 hash of the participant bearer token, issued once at join and
    # required to submit ideas / vote / open the SSE stream. Nullable for
    # back-compat with rows created before participant auth existed.
    token_hash: Mapped[str | None] = mapped_column(String, nullable=True, default=None)


class SessionDB(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    topic: Mapped[str] = mapped_column(String)
    framework: Mapped[str] = mapped_column(String, default="swot")
    custom_categories: Mapped[dict] = mapped_column(JSON, default=list)
    access_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # SHA-256 hash of the facilitator bearer token. Nullable for back-compat
    # with sessions created before tokens were introduced.
    facilitator_token_hash: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    participants: Mapped[list["ParticipantDB"]] = relationship(backref="session")


class IdeaDB(Base):
    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    participant_id: Mapped[str] = mapped_column(String)
    participant_name: Mapped[str] = mapped_column(String, default="")
    category: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    content: Mapped[str] = mapped_column(Text)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class AnalysisDB(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), unique=True)
    framework: Mapped[str] = mapped_column(String)
    categories: Mapped[dict] = mapped_column(JSON)
    key_themes: Mapped[list] = mapped_column(JSON, default=list)
    decisions_made: Mapped[list] = mapped_column(JSON, default=list)
    open_questions: Mapped[list] = mapped_column(JSON, default=list)
    recommended_next_steps: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
