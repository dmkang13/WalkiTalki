from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class LessonSession(Base):
    __tablename__ = "lesson_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    runtime_session_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    agent_spec_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_specs.id"), nullable=False)
    share_slug: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    image_mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    image_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    image_storage_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lesson_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    openai_initial_response_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    agent_spec = relationship("AgentSpec", back_populates="lesson_sessions")
    messages = relationship("ChatMessage", back_populates="lesson_session", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="lesson_session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lesson_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lesson_sessions.id"), nullable=False, index=True)
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    openai_response_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lesson_session = relationship("LessonSession", back_populates="messages")


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lesson_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lesson_sessions.id"), nullable=False, index=True)
    openai_response_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    lesson_session = relationship("LessonSession", back_populates="usage_events")
