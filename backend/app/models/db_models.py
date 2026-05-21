import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ParticipantDB(Base):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    name: Mapped[str] = mapped_column(String)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class SessionDB(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    topic: Mapped[str] = mapped_column(String)
    framework: Mapped[str] = mapped_column(String, default="swot")
    custom_categories: Mapped[dict] = mapped_column(JSON, default=list)
    access_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
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
