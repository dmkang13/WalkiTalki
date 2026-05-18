from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException


@dataclass
class SessionRecord:
    browser_session_id: str
    openclaw_session_id: str
    agent_id: str
    runtime_status: str
    provider_status: str
    login_url: Optional[str]
    model: Optional[str]
    provider: Optional[str]
    custom_instructions: Optional[str]
    skill_status: str = "unknown"
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class SessionStore:
    def __init__(self) -> None:
        self._records: Dict[str, SessionRecord] = {}

    def create_browser_session_id(self) -> str:
        return "browser_" + uuid4().hex

    def start_session(
        self,
        browser_session_id: str,
        agent_id: str,
        openclaw_session_id: str,
        custom_instructions: Optional[str],
        runtime_status: str,
        provider_status: str,
        login_url: Optional[str],
        model: Optional[str],
        provider: Optional[str],
    ) -> SessionRecord:
        record = SessionRecord(
            browser_session_id=browser_session_id,
            openclaw_session_id=openclaw_session_id,
            agent_id=agent_id,
            runtime_status=runtime_status,
            provider_status=provider_status,
            login_url=login_url,
            model=model,
            provider=provider,
            custom_instructions=custom_instructions,
        )
        self._records[browser_session_id] = record
        return record

    def require_session(self, browser_session_id: str) -> SessionRecord:
        record = self._records.get(browser_session_id)
        if record is None:
            raise HTTPException(status_code=404, detail="No OpenClaw session exists.")
        return record

    def require_ready_session(self, browser_session_id: str) -> SessionRecord:
        record = self.require_session(browser_session_id)
        if record.runtime_status != "ready" or record.provider_status != "connected":
            raise HTTPException(status_code=409, detail="Provider login is required.")
        return record

    def update_runtime(
        self,
        browser_session_id: str,
        runtime_status: str,
        provider_status: str,
        login_url: Optional[str],
        model: Optional[str],
        provider: Optional[str],
    ) -> SessionRecord:
        record = self.require_session(browser_session_id)
        record.runtime_status = runtime_status
        record.provider_status = provider_status
        record.login_url = login_url
        record.model = model
        record.provider = provider
        record.updated_at = datetime.utcnow()
        return record

    def update_skill_status(self, browser_session_id: str, status: str) -> SessionRecord:
        record = self.require_session(browser_session_id)
        record.skill_status = status
        record.updated_at = datetime.utcnow()
        return record

    def append_message(self, browser_session_id: str, role: str, content: str) -> None:
        record = self.require_session(browser_session_id)
        record.messages.append({"role": role, "content": content})
        record.updated_at = datetime.utcnow()

    def reset(self, browser_session_id: str) -> None:
        self._records.pop(browser_session_id, None)
