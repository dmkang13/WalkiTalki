from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_session
from app.core.config import settings
from app.core.errors import raise_api_error
from app.core.session import api_key_store
from app.db.session import get_db
from app.models.agent import AgentSpec, AgentStatus
from app.models.lesson import ChatMessage, ChatRole, LessonSession, UsageEvent
from app.schemas.agents import SharedAgentRead
from app.schemas.lessons import LessonSessionRead
from app.services.openai_client import OpenAIInvalidKeyError, OpenAIUnavailableError, openai_client
from app.services.prompts import build_initial_lesson_prompt

router = APIRouter(prefix="/shared-agents", tags=["shared-agents"])

SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


@router.get("/{share_slug}", response_model=SharedAgentRead, response_model_by_alias=True)
def get_shared_agent(share_slug: str, db: Session = Depends(get_db)) -> AgentSpec:
    agent = _published_agent_by_slug(db, share_slug)
    return agent


@router.post("/{share_slug}/lesson-sessions", response_model=LessonSessionRead, response_model_by_alias=True)
async def create_lesson_session(
    share_slug: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    session: tuple = Depends(current_session),
) -> LessonSessionRead:
    session_id, runtime_hash = session
    api_key = api_key_store.get_key(session_id)
    if not api_key:
        raise_api_error(401, "missing_api_key", "Connect your OpenAI API key before generating a lesson.")

    agent = _published_agent_by_slug(db, share_slug)
    image_bytes = await image.read()
    mime_type = image.content_type or ""
    _validate_image(mime_type, image_bytes)

    try:
        result = openai_client.create_initial_lesson(
            api_key=api_key,
            prompt=build_initial_lesson_prompt(agent),
            image_bytes=image_bytes,
            mime_type=mime_type,
        )
    except OpenAIInvalidKeyError:
        raise_api_error(401, "invalid_api_key", "Reconnect your OpenAI API key before generating a lesson.")
    except OpenAIUnavailableError:
        raise_api_error(502, "openai_request_failed", "OpenAI could not generate a lesson from this image.")

    lesson = LessonSession(
        runtime_session_hash=runtime_hash,
        agent_spec_id=agent.id,
        share_slug=share_slug,
        image_mime_type=mime_type,
        image_size_bytes=len(image_bytes),
        lesson_markdown=result.content,
        openai_initial_response_id=result.response_id,
    )
    db.add(lesson)
    db.flush()

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
    db.refresh(lesson)
    db.refresh(assistant)
    return _lesson_response(lesson, [assistant], usage)


def _published_agent_by_slug(db: Session, share_slug: str) -> AgentSpec:
    agent = db.scalar(select(AgentSpec).where(AgentSpec.share_slug == share_slug))
    if not agent:
        raise_api_error(404, "agent_not_found", "Shared agent not found.")
    if agent.status != AgentStatus.published:
        raise_api_error(404, "agent_not_published", "Shared agent is not published.")
    return agent


def _validate_image(mime_type: str, image_bytes: bytes) -> None:
    if mime_type not in SUPPORTED_IMAGE_TYPES:
        raise_api_error(400, "invalid_image_type", "Upload a PNG, JPEG, WEBP, or GIF image.")
    if len(image_bytes) > settings.max_image_bytes:
        raise_api_error(400, "image_too_large", "Image uploads must be 10 MB or smaller.")
    if not image_bytes:
        raise_api_error(400, "invalid_image_type", "Upload a non-empty image file.")


def _usage_event(lesson_id, result):
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


def _lesson_response(lesson: LessonSession, messages, usage: Optional[UsageEvent]) -> LessonSessionRead:
    return LessonSessionRead(
        id=lesson.id,
        agent_id=lesson.agent_spec_id,
        lesson_markdown=lesson.lesson_markdown,
        usage=usage,
        messages=messages,
    )
