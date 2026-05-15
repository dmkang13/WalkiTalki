from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import current_session
from app.core.errors import raise_api_error
from app.core.session import api_key_store
from app.schemas.runtime import OpenAIKeyStatus, OpenAIKeyValidateRequest
from app.services.openai_client import OpenAIInvalidKeyError, OpenAIUnavailableError, openai_client

router = APIRouter(prefix="/runtime/openai-key", tags=["runtime"])


@router.post("/validate", response_model=OpenAIKeyStatus, response_model_by_alias=True)
def validate_openai_key(
    payload: OpenAIKeyValidateRequest,
    session: tuple = Depends(current_session),
) -> OpenAIKeyStatus:
    session_id, _ = session
    api_key = (payload.api_key or "").strip()
    if not api_key:
        raise_api_error(400, "missing_api_key", "Provide an OpenAI API key.")
    try:
        openai_client.validate_api_key(api_key)
    except OpenAIInvalidKeyError:
        raise_api_error(401, "invalid_api_key", "The OpenAI API key was rejected.")
    except OpenAIUnavailableError:
        raise_api_error(502, "openai_request_failed", "OpenAI validation is unavailable right now.")
    api_key_store.set_key(session_id, api_key)
    return OpenAIKeyStatus(has_api_key=True)


@router.get("/status", response_model=OpenAIKeyStatus, response_model_by_alias=True)
def openai_key_status(session: tuple = Depends(current_session)) -> OpenAIKeyStatus:
    session_id, _ = session
    return OpenAIKeyStatus(has_api_key=api_key_store.has_key(session_id))


@router.delete("", response_model=OpenAIKeyStatus, response_model_by_alias=True)
def delete_openai_key(session: tuple = Depends(current_session)) -> OpenAIKeyStatus:
    session_id, _ = session
    api_key_store.delete_key(session_id)
    return OpenAIKeyStatus(has_api_key=False)
