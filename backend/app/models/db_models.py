import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ParticipantDB(Base):
    __tablename__ = "participants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    name: Mapped[str] = mapped_column(String)


class SessionDB(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    topic: Mapped[str] = mapped_column(String)
    framework: Mapped[str] = mapped_column(String, default="swot")
    custom_categories: Mapped[dict] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    participants: Mapped[list["ParticipantDB"]] = relationship(backref="session")


class IdeaDB(Base):
    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))
    participant_id: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AnalysisDB(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), unique=True)
    framework: Mapped[str] = mapped_column(String)
    categories: Mapped[dict] = mapped_column(JSON)
    key_themes: Mapped[dict] = mapped_column(JSON, default=list)
    decisions_made: Mapped[dict] = mapped_column(JSON, default=list)
    open_questions: Mapped[dict] = mapped_column(JSON, default=list)
    recommended_next_steps: Mapped[dict] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
