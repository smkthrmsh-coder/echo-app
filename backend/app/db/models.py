import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    prompt: Mapped[str] = mapped_column(Text)
    experience_title: Mapped[str] = mapped_column(String(255), default="")
    tone: Mapped[str] = mapped_column(String(64), default="")
    narration_style: Mapped[str] = mapped_column(String(64), default="")
    pacing: Mapped[str] = mapped_column(String(32), default="")
    voice_id: Mapped[str] = mapped_column(String(128), default="")
    voice_name: Mapped[str] = mapped_column(String(128), default="")
    ambience_prompt: Mapped[str] = mapped_column(Text, default="")
    music_category: Mapped[str] = mapped_column(String(64), default="")
    script: Mapped[str] = mapped_column(Text, default="")
    audio_path: Mapped[str] = mapped_column(String(512), default="")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    speaking_styles: Mapped[str] = mapped_column(Text, default="[]")  # JSON array of persona IDs
    gender: Mapped[str] = mapped_column(String(16), default="female")
    energy_level: Mapped[int] = mapped_column(Integer, default=3)
    persona_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # chosen Echo persona
    emotion: Mapped[str | None] = mapped_column(String(64), nullable=True)     # initial emotion card
    voice_id: Mapped[str] = mapped_column(String(128), default="")             # locked voice for continuity
    voice_name: Mapped[str] = mapped_column(String(128), default="")           # display name of locked voice
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    journey_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # linked journey
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, default="")
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    voice_name: Mapped[str] = mapped_column(String(128), default="")
    tone: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="general")  # goals, habits, wins, etc.
    source_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_conversation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserJourney(Base):
    """Tracks a user's progress through a journey program."""
    __tablename__ = "user_journeys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    journey_slug: Mapped[str] = mapped_column(String(64), index=True)
    current_day: Mapped[int] = mapped_column(Integer, default=1)
    completed_days: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of completed day numbers
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_session_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DailyStreak(Base):
    """One row per day the user had a conversation. Drives streak calculation."""
    __tablename__ = "daily_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(10), unique=True, index=True)  # "YYYY-MM-DD"
    conversation_count: Mapped[int] = mapped_column(Integer, default=1)
