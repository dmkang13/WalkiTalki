from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import current_session
from app.core.errors import raise_api_error
from app.core.session import api_key_store
from app.db.session import get_db
from app.models.lesson import ChatMessage, ChatRole, LessonSession, UsageEvent
from app.schemas.lessons import LessonSessionRead, MessageCreate, MessageCreateRead
from app.services.openai_client import OpenAIInvalidKeyError, OpenAIUnavailableError, openai_client
from app.services.prompts import build_followup_prompt

router = APIRouter(prefix="/lesson-sessions", tags=["lesson-sessions"])


@router.get("/{lesson_session_id}", response_model=LessonSessionRead, response_model_by_alias=True)
def get_lesson_session(
    lesson_session_id: UUID,
    db: Session = Depends(get_db),
    session: tuple = Depends(current_session),
) -> LessonSessionRead:
    _, runtime_hash = session
    lesson = _owned_lesson(db, lesson_session_id, runtime_hash)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.lesson_session_id == lesson.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()
    usage = _latest_usage(db, lesson.id)
    return LessonSessionRead(
        id=lesson.id,
        agent_id=lesson.agent_spec_id,
        lesson_markdown=lesson.lesson_markdown,
        usage=usage,
        messages=messages,
    )


@router.post("/{lesson_session_id}/messages", response_model=MessageCreateRead, response_model_by_alias=True)
def create_message(
    lesson_session_id: UUID,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    session: tuple = Depends(current_session),
) -> MessageCreateRead:
    session_id, runtime_hash = session
    api_key = api_key_store.get_key(session_id)
    if not api_key:
        raise_api_error(401, "missing_api_key", "Connect your OpenAI API key before continuing the lesson.")

    lesson = _owned_lesson(db, lesson_session_id, runtime_hash)
    prior_messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.lesson_session_id == lesson.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()

    user_message = ChatMessage(
        lesson_session_id=lesson.id,
        role=ChatRole.user,
        content=payload.content.strip(),
    )
    db.add(user_message)
    db.flush()

    try:
        result = openai_client.create_followup(
            api_key=api_key,
            prompt=build_followup_prompt(lesson.agent_spec, lesson.lesson_markdown, prior_messages, payload.content.strip()),
        )
    except OpenAIInvalidKeyError:
        raise_api_error(401, "invalid_api_key", "Reconnect your OpenAI API key before continuing the lesson.")
    except OpenAIUnavailableError:
        raise_api_error(502, "openai_request_failed", "OpenAI could not answer this follow-up.")

    assistant = ChatMessage(
        lesson_session_id=lesson.id,
        role=ChatRole.assistant,
        content=result.content,
        openai_response_id=result.response_id,
    )
    db.add(assistant)
    usage = _usage_event(lesson.id, result)
    if usage:
        db.add(usage)
    db.commit()
    db.refresh(assistant)
    return MessageCreateRead(message=assistant, usage=usage)


def _owned_lesson(db: Session, lesson_session_id: UUID, runtime_hash: str) -> LessonSession:
    lesson = db.scalar(
        select(LessonSession)
        .options(selectinload(LessonSession.agent_spec))
        .where(LessonSession.id == lesson_session_id)
    )
    if not lesson or lesson.runtime_session_hash != runtime_hash:
        raise_api_error(404, "lesson_session_not_found", "Lesson session not found.")
    return lesson


def _latest_usage(db: Session, lesson_id: UUID) -> Optional[UsageEvent]:
    return db.scalar(
        select(UsageEvent)
        .where(UsageEvent.lesson_session_id == lesson_id)
        .order_by(UsageEvent.created_at.desc())
        .limit(1)
    )


def _usage_event(lesson_id: UUID, result):
    if all(value is None for value in [result.model, result.input_tokens, result.output_tokens, result.total_tokens]):
        return None
    return UsageEvent(
        lesson_session_id=lesson_id,
        openai_response_id=result.response_id,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
    )
