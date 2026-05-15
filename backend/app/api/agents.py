from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_session
from app.core.config import settings
from app.core.errors import raise_api_error
from app.db.session import get_db
from app.models.agent import AgentSpec, AgentStatus
from app.schemas.agents import AgentCreate, AgentPublishRead, AgentRead, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentRead, response_model_by_alias=True)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    session: tuple = Depends(current_session),
) -> AgentSpec:
    _, owner_hash = session
    agent = AgentSpec(
        owner_session_hash=owner_hash,
        name=payload.name.strip(),
        target_language=payload.target_language.strip(),
        native_language=_clean_optional(payload.native_language),
        custom_instructions=_clean_optional(payload.custom_instructions),
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/{agent_id}", response_model=AgentRead, response_model_by_alias=True)
def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
    session: tuple = Depends(current_session),
) -> AgentSpec:
    _, owner_hash = session
    agent = db.get(AgentSpec, agent_id)
    if not agent or agent.owner_session_hash != owner_hash:
        raise_api_error(404, "agent_not_found", "Agent not found.")
    if agent.status == AgentStatus.published:
        raise_api_error(409, "agent_already_published", "Published agents cannot be edited in the MVP.")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        if key in {"native_language", "custom_instructions"}:
            value = _clean_optional(value)
        setattr(agent, key, value)
    db.commit()
    db.refresh(agent)
    return agent


@router.post("/{agent_id}/publish", response_model=AgentPublishRead, response_model_by_alias=True)
def publish_agent(
    agent_id: UUID,
    db: Session = Depends(get_db),
    session: tuple = Depends(current_session),
) -> AgentPublishRead:
    _, owner_hash = session
    agent = db.get(AgentSpec, agent_id)
    if not agent or agent.owner_session_hash != owner_hash:
        raise_api_error(404, "agent_not_found", "Agent not found.")

    if agent.status != AgentStatus.published:
        agent.share_slug = _unique_share_slug(db)
        agent.status = AgentStatus.published
        agent.published_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(agent)

    return AgentPublishRead(
        id=agent.id,
        status=agent.status.value,
        share_slug=agent.share_slug,
        share_url=f"{settings.app_base_url.rstrip('/')}/agents/{agent.share_slug}",
    )


def _clean_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _unique_share_slug(db: Session) -> str:
    for _ in range(12):
        slug = secrets.token_urlsafe(18).rstrip("=")
        existing = db.scalar(select(AgentSpec.id).where(AgentSpec.share_slug == slug))
        if existing is None:
            return slug
    raise_api_error(500, "share_slug_failed", "Could not create a share link. Try again.")
