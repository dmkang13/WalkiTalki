from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ExampleAgent(BaseModel):
    agent_id: str
    name: str
    description: str
    target_language: str
    native_language: Optional[str] = None
    instructions: str
    required_capabilities: List[str]
    validation_skill_id: str
    validation_skill_name: str
    validation_skill_source: str


class AgentSummary(BaseModel):
    agent_id: str
    name: str
    description: str
    target_language: str
    native_language: Optional[str]
    required_capabilities: List[str]
    validation_skill_name: str
    validation_skill_source: str

    @classmethod
    def from_agent(cls, agent: ExampleAgent) -> "AgentSummary":
        return cls(
            agent_id=agent.agent_id,
            name=agent.name,
            description=agent.description,
            target_language=agent.target_language,
            native_language=agent.native_language,
            required_capabilities=agent.required_capabilities,
            validation_skill_name=agent.validation_skill_name,
            validation_skill_source=agent.validation_skill_source,
        )


class SessionStartRequest(BaseModel):
    custom_instructions: Optional[str] = Field(default=None, max_length=2000)


class AuthStatusRead(BaseModel):
    provider_status: str
    login_url: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    diagnostic: Optional[str] = None


class SessionRead(BaseModel):
    local_session_id: str
    openclaw_session_id: str
    agent_id: str
    runtime_status: str
    provider_status: str
    login_url: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    custom_instructions_provided: bool
    skill_status: str

    @classmethod
    def from_record(cls, record: "SessionRecordLike") -> "SessionRead":
        return cls(
            local_session_id=record.browser_session_id,
            openclaw_session_id=record.openclaw_session_id,
            agent_id=record.agent_id,
            runtime_status=record.runtime_status,
            provider_status=record.provider_status,
            login_url=record.login_url,
            model=record.model,
            provider=record.provider,
            custom_instructions_provided=bool(record.custom_instructions),
            skill_status=record.skill_status,
        )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    message: str
    runtime_status: str
    provider_status: str
    usage: Optional[Dict[str, int]] = None


class ImageLessonResponse(ChatResponse):
    image_upload_status: str


class SkillValidationResponse(BaseModel):
    message: str
    skill_status: str
    skill_name: str
    skill_source: str
    evidence: str


class ResetResponse(BaseModel):
    ok: bool


class ErrorResponse(BaseModel):
    code: str
    message: str
    retryable: bool = False


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    target_language: str = Field(min_length=1, max_length=80)
    native_language: Optional[str] = Field(default=None, max_length=80)
    custom_instructions: Optional[str] = Field(default=None, max_length=1000)


class AgentRead(BaseModel):
    id: str
    name: str
    description: str
    target_language: str
    native_language: Optional[str] = None
    custom_instructions: Optional[str] = None
    status: str
    share_slug: Optional[str] = None


class AgentListResponse(BaseModel):
    agents: List[AgentRead]


class AgentPublishResponse(BaseModel):
    id: str
    status: str
    share_slug: str
    share_url: str


class SessionRecordLike:
    browser_session_id: str
    openclaw_session_id: str
    agent_id: str
    runtime_status: str
    provider_status: str
    login_url: Optional[str]
    model: Optional[str]
    provider: Optional[str]
    custom_instructions: Optional[str]
    skill_status: str
