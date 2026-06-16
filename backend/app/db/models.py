import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), default="")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    speaking_styles: Mapped[str] = mapped_column(Text, default="[]")
    gender: Mapped[str] = mapped_column(String(16), default="female")
    energy_level: Mapped[int] = mapped_column(Integer, default=3)
    persona_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    voice_id: Mapped[str] = mapped_column(String(128), default="")
    voice_name: Mapped[str] = mapped_column(String(128), default="")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    journey_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    summarized_through_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text, default="")
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    voice_name: Mapped[str] = mapped_column(String(128), default="")
    tone: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="general")
    source_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_conversation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BrainMemory(Base):
    __tablename__ = "brain_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    category: Mapped[str] = mapped_column(String(64), default="general")
    lifecycle: Mapped[str] = mapped_column(String(32), default="semi_permanent")
    status: Mapped[str] = mapped_column(String(32), default="active")
    title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    importance: Mapped[str] = mapped_column(String(32), default="medium")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    valid_from: Mapped[str | None] = mapped_column(String(10), nullable=True)
    valid_until: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserJourney(Base):
    """Tracks a user's progress through a journey program."""
    __tablename__ = "user_journeys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    journey_slug: Mapped[str] = mapped_column(String(64), index=True)
    current_day: Mapped[int] = mapped_column(Integer, default=1)
    completed_days: Mapped[str] = mapped_column(Text, default="[]")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_session_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DailyStreak(Base):
    """One row per day the user had a conversation. Drives streak calculation."""
    __tablename__ = "daily_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_str: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    conversation_count: Mapped[int] = mapped_column(Integer, default=1)
