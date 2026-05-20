import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.openclaw import AgentRead, ExampleAgent


@dataclass
class AgentRecord:
    id: str
    owner_browser_session_id: str
    name: str
    target_language: str
    native_language: Optional[str]
    custom_instructions: Optional[str]
    status: str
    share_slug: Optional[str]
    created_at: datetime
    published_at: Optional[datetime]


class AgentStore:
    def __init__(self) -> None:
        self._agents: Dict[str, AgentRecord] = {}
        self._share_index: Dict[str, str] = {}

    def create(
        self,
        browser_session_id: str,
        name: str,
        target_language: str,
        native_language: Optional[str],
        custom_instructions: Optional[str],
    ) -> AgentRecord:
        record = AgentRecord(
            id=str(uuid4()),
            owner_browser_session_id=browser_session_id,
            name=name.strip(),
            target_language=target_language.strip(),
            native_language=self._clean_optional(native_language),
            custom_instructions=self._clean_optional(custom_instructions),
            status="draft",
            share_slug=None,
            created_at=datetime.utcnow(),
            published_at=None,
        )
        self._agents[record.id] = record
        return record

    def publish(self, agent_id: str, browser_session_id: str) -> AgentRecord:
        record = self._agents.get(agent_id)
        if record is None or record.owner_browser_session_id != browser_session_id:
            raise HTTPException(status_code=404, detail="Agent not found.")
        if record.status == "published" and record.share_slug:
            return record

        share_slug = self._unique_share_slug()
        record.status = "published"
        record.share_slug = share_slug
        record.published_at = datetime.utcnow()
        self._share_index[share_slug] = record.id
        return record

    def list_published(self) -> List[AgentRecord]:
        return sorted(
            [record for record in self._agents.values() if record.status == "published"],
            key=lambda record: record.published_at or record.created_at,
            reverse=True,
        )

    def require_published(self, share_slug: str) -> AgentRecord:
        agent_id = self._share_index.get(share_slug)
        record = self._agents.get(agent_id) if agent_id else None
        if record is None or record.status != "published":
            raise HTTPException(status_code=404, detail="Published agent not found.")
        return record

    def to_read(self, record: AgentRecord) -> AgentRead:
        return AgentRead(
            id=record.id,
            name=record.name,
            description=self._description(record),
            target_language=record.target_language,
            native_language=record.native_language,
            custom_instructions=record.custom_instructions,
            status=record.status,
            share_slug=record.share_slug,
        )

    def to_example_agent(self, record: AgentRecord) -> ExampleAgent:
        native = record.native_language or "the learner's native language"
        instructions = (
            f"You are {record.name}, a WalkiTalki language tutor. "
            f"Help the user practice {record.target_language}. "
            f"Explain vocabulary and phrases in {native}. "
            "Keep answers practical, concise, and grounded in the user's current request. "
            "Do not claim to save flashcards, progress, memory, vocabulary, or lesson history."
        )
        if record.custom_instructions:
            instructions += f"\nPublished agent custom instructions: {record.custom_instructions}"

        return ExampleAgent(
            agent_id=record.id,
            name=record.name,
            description=self._description(record),
            target_language=record.target_language,
            native_language=record.native_language,
            instructions=instructions,
            required_capabilities=["text_chat", "openclaw_runtime"],
            validation_skill_id="text-language-tutor",
            validation_skill_name="Text Language Tutor",
            validation_skill_source="OpenClaw MVP in-memory agent",
        )

    def _unique_share_slug(self) -> str:
        for _ in range(12):
            slug = secrets.token_urlsafe(12).rstrip("=")
            if slug not in self._share_index:
                return slug
        raise HTTPException(status_code=500, detail="Could not create a share link.")

    def _description(self, record: AgentRecord) -> str:
        native = f" with explanations in {record.native_language}" if record.native_language else ""
        return f"A text language tutor for practicing {record.target_language}{native}."

    def _clean_optional(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

