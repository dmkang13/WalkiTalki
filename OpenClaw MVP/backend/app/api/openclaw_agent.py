from typing import Optional

from fastapi import APIRouter, Cookie, File, Response, UploadFile

from app.schemas.openclaw import (
    AgentSummary,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ImageLessonResponse,
    ResetResponse,
    SessionRead,
    SessionStartRequest,
    SkillValidationResponse,
)
from app.services.example_agent import get_example_agent
from app.services.openclaw_client import MockOpenClawClient
from app.services.openclaw_sessions import SessionStore

router = APIRouter()
session_store = SessionStore()
openclaw_client = MockOpenClawClient()

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


@router.post("/session", response_model=SessionRead)
def start_session(
    payload: SessionStartRequest,
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SessionRead:
    browser_id = get_browser_session_id(response, browser_session_id)
    agent = get_example_agent()
    runtime = openclaw_client.create_session(agent, payload.custom_instructions)
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
    runtime = openclaw_client.confirm_login(record.openclaw_session_id)
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
    result = openclaw_client.send_text(record.openclaw_session_id, payload.message)
    session_store.append_message(browser_id, "user", payload.message)
    session_store.append_message(browser_id, "assistant", result.message)
    return ChatResponse(
        message=result.message,
        runtime_status=record.runtime_status,
        provider_status=record.provider_status,
        usage=result.usage,
    )


@router.post("/image-lesson", response_model=ImageLessonResponse)
async def send_image_lesson(
    response: Response,
    image: UploadFile = File(...),
    prompt: Optional[str] = None,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> ImageLessonResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_ready_session(browser_id)
    image_bytes = await image.read()
    result = openclaw_client.send_image_lesson(
        session_id=record.openclaw_session_id,
        filename=image.filename or "uploaded-image",
        content_type=image.content_type or "application/octet-stream",
        byte_count=len(image_bytes),
        prompt=prompt,
    )
    session_store.append_message(
        browser_id,
        "user",
        "Uploaded an image for a language lesson.",
    )
    session_store.append_message(browser_id, "assistant", result.message)
    return ImageLessonResponse(
        message=result.message,
        image_upload_status="routed_to_target_llm",
        runtime_status=record.runtime_status,
        provider_status=record.provider_status,
        usage=result.usage,
    )


@router.post("/skill-validation", response_model=SkillValidationResponse)
def validate_skill(
    response: Response,
    browser_session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> SkillValidationResponse:
    browser_id = get_browser_session_id(response, browser_session_id)
    record = session_store.require_ready_session(browser_id)
    result = openclaw_client.invoke_validation_skill(record.openclaw_session_id)
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
