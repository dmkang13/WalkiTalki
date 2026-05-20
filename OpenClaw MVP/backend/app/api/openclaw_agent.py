import json
import os
from typing import Iterator, Optional

from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.schemas.openclaw import (
    AgentCreateRequest,
    AgentListResponse,
    AgentPublishResponse,
    AgentRead,
    AgentSummary,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ResetResponse,
    SessionRead,
    SessionStartRequest,
    SkillValidationResponse,
)
from app.services.agent_store import AgentStore
from app.services.example_agent import get_example_agent
from app.services.openclaw_client import OpenClawClient, OpenClawError
from app.services.openclaw_sessions import SessionStore

router = APIRouter()
session_store = SessionStore()
agent_store = AgentStore()
openclaw_client = OpenClawClient()

SESSION_COOKIE = "openclaw_browser_session"


def get_browser_session_id(response: Response, existing: Optional[str]) -> str:
    session_id = existing or session_store.create_browser_session_id()
    if not existing:
        response.set_cookie(
            key=SESSION_COOKIE,
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 8,
        )
    return session_id


@router.get("/agent", response_model=AgentSummary)
def read_agent() -> AgentSummary:
    return AgentSummary.from_agent(get_example_agent())


@router.post("/agents", response_model=AgentRead)
def create_agent(
    payload: AgentCreateRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> AgentRead:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = agent_store.create(
        browser_session_id=browser_id,
        name=payload.name,
        target_language=payload.target_language,
        native_language=payload.native_language,
        custom_instructions=payload.custom_instructions,
    )
    return agent_store.to_read(record)


@router.get("/agents", response_model=AgentListResponse)
def list_agents() -> AgentListResponse:
    return AgentListResponse(agents=[agent_store.to_read(record) for record in agent_store.list_published()])


@router.get("/agents/{share_slug}", response_model=AgentRead)
def read_shared_agent(share_slug: str) -> AgentRead:
    return agent_store.to_read(agent_store.require_published(share_slug))


@router.post("/agents/{agent_id}/publish", response_model=AgentPublishResponse)
def publish_agent(
    agent_id: str,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> AgentPublishResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = agent_store.publish(agent_id, browser_id)
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:5174").rstrip("/")
    return AgentPublishResponse(
        id=record.id,
        status=record.status,
        share_slug=record.share_slug or "",
        share_url=f"{base_url}/agents/{record.share_slug}",
    )


@router.post("/session", response_model=SessionRead)
def start_session(
    payload: SessionStartRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionRead:
    browser_id = get_browser_session_id(response, browser_session_id)
    agent = get_example_agent()
    try:
        runtime = openclaw_client.create_session(agent, payload.custom_instructions)
    except OpenClawError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message}) from exc
    record = session_store.start_session(
        browser_session_id=browser_id,
        agent_id=agent.agent_id,
        openclaw_session_id=runtime.openclaw_session_id,
        custom_instructions=payload.custom_instructions,
        runtime_status=runtime.runtime_status,
        provider_status=runtime.provider_status,
        login_url=runtime.login_url,
        model=runtime.model,
        provider=runtime.provider,
    )
    return SessionRead.from_record(record)


@router.post("/agents/{share_slug}/session", response_model=SessionRead)
def start_agent_session(
    share_slug: str,
    payload: SessionStartRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionRead:
    browser_id = get_browser_session_id(response, browser_session_id)
    agent_record = agent_store.require_published(share_slug)
    agent = agent_store.to_example_agent(agent_record)
    try:
        runtime = openclaw_client.create_session(agent, payload.custom_instructions)
    except OpenClawError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message}) from exc
    record = session_store.start_session(
        browser_session_id=browser_id,
        agent_id=agent.agent_id,
        openclaw_session_id=runtime.openclaw_session_id,
        custom_instructions=payload.custom_instructions,
        runtime_status=runtime.runtime_status,
        provider_status=runtime.provider_status,
        login_url=runtime.login_url,
        model=runtime.model,
        provider=runtime.provider,
    )
    return SessionRead.from_record(record)


@router.post("/session/confirm-login", response_model=SessionRead)
def confirm_login(
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionRead:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_session(browser_id)
    try:
        runtime = openclaw_client.confirm_login(record.openclaw_session_id)
    except OpenClawError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message}) from exc
    updated = session_store.update_runtime(
        browser_id,
        runtime_status=runtime.runtime_status,
        provider_status=runtime.provider_status,
        login_url=runtime.login_url,
        model=runtime.model,
        provider=runtime.provider,
    )
    return SessionRead.from_record(updated)


@router.post("/chat", response_model=ChatResponse)
def send_chat(
    payload: ChatRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> ChatResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_ready_session(browser_id)
    try:
        result = openclaw_client.send_text(record.openclaw_session_id, payload.message)
    except OpenClawError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message}) from exc
    session_store.append_message(browser_id, "user", payload.message)
    session_store.append_message(browser_id, "assistant", result.message)
    return ChatResponse(
        message=result.message,
        runtime_status=record.runtime_status,
        provider_status=record.provider_status,
        usage=result.usage,
    )


@router.post("/chat/stream")
def stream_chat(
    payload: ChatRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> StreamingResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_ready_session(browser_id)
    session_store.append_message(browser_id, "user", payload.message)

    def events() -> Iterator[str]:
        chunks: list[str] = []
        try:
            for event in openclaw_client.stream_text(record.openclaw_session_id, payload.message):
                if event.get("type") == "delta":
                    text = str(event.get("text") or "")
                    chunks.append(text)
                yield json.dumps(event) + "\n"
        except OpenClawError as exc:
            yield json.dumps(
                {
                    "type": "error",
                    "code": exc.code,
                    "message": exc.message,
                }
            ) + "\n"
            return

        assistant_message = "".join(chunks)
        if assistant_message:
            session_store.append_message(browser_id, "assistant", assistant_message)

    return StreamingResponse(events(), media_type="application/x-ndjson")


@router.post("/agents/{share_slug}/chat/stream")
def stream_agent_chat(
    share_slug: str,
    payload: ChatRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> StreamingResponse:
    agent_store.require_published(share_slug)
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_ready_session(browser_id)

    def events() -> Iterator[str]:
        try:
            for event in openclaw_client.stream_text(record.openclaw_session_id, payload.message):
                yield json.dumps(event) + "\n"
        except OpenClawError as exc:
            yield json.dumps(
                {
                    "type": "error",
                    "code": exc.code,
                    "message": exc.message,
                }
            ) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")


@router.post("/skill-validation", response_model=SkillValidationResponse)
def validate_skill(
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SkillValidationResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_ready_session(browser_id)
    try:
        result = openclaw_client.invoke_validation_skill(record.openclaw_session_id)
    except OpenClawError as exc:
        raise HTTPException(status_code=503, detail={"code": exc.code, "message": exc.message}) from exc
    updated = session_store.update_skill_status(browser_id, "invoked")
    session_store.append_message(browser_id, "assistant", result.message)
    return SkillValidationResponse(
        message=result.message,
        skill_status=updated.skill_status,
        skill_name=result.skill_name,
        skill_source=result.skill_source,
        evidence=result.evidence,
    )


@router.post("/session/reset", response_model=ResetResponse)
def reset_session(
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> ResetResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    session_store.reset(browser_id)
    return ResetResponse(ok=True)


@router.get("/session", response_model=SessionRead)
def read_session(
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionRead:
    browser_id = get_browser_session_id(response, browser_session_id)
    return SessionRead.from_record(session_store.require_session(browser_id))


@router.get("/errors/example", response_model=ErrorResponse)
def read_error_example() -> ErrorResponse:
    return ErrorResponse(
        code="runtime_unavailable",
        message="OpenClaw is unavailable. Try again after the runtime is configured.",
        retryable=True,
    )
