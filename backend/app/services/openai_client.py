import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.config import settings


class OpenAIClientError(Exception):
    pass


class OpenAIUnavailableError(OpenAIClientError):
    pass


class OpenAIInvalidKeyError(OpenAIClientError):
    pass


@dataclass
class OpenAIResult:
    content: str
    response_id: Optional[str]
    model: Optional[str]
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class OpenAIClient:
    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or settings.openai_default_model

    def validate_api_key(self, api_key: str) -> bool:
        client = self._client(api_key)
        try:
            # Keep validation independent of the configured chat/vision model.
            # A user's key can be valid even if the default MVP model is wrong,
            # unavailable to that project, or temporarily quota-limited.
            client.models.list()
            return True
        except Exception as exc:
            if self._is_auth_error(exc):
                raise OpenAIInvalidKeyError("Invalid OpenAI API key.") from exc
            raise OpenAIUnavailableError("OpenAI validation is unavailable.") from exc

    def create_initial_lesson(self, api_key: str, prompt: str, image_bytes: bytes, mime_type: str) -> OpenAIResult:
        client = self._client(api_key)
        image_data = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{image_data}"
        try:
            response = client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": data_url},
                        ],
                    }
                ],
            )
            return self._result(response)
        except Exception as exc:
            if self._is_auth_error(exc):
                raise OpenAIInvalidKeyError("Invalid OpenAI API key.") from exc
            raise OpenAIUnavailableError("OpenAI could not generate the lesson.") from exc

    def create_followup(self, api_key: str, prompt: str) -> OpenAIResult:
        client = self._client(api_key)
        try:
            response = client.responses.create(
                model=self.model,
                input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            )
            return self._result(response)
        except Exception as exc:
            if self._is_auth_error(exc):
                raise OpenAIInvalidKeyError("Invalid OpenAI API key.") from exc
            raise OpenAIUnavailableError("OpenAI could not answer the follow-up.") from exc

    @staticmethod
    def _client(api_key: str) -> Any:
        try:
            from openai import OpenAI
        except Exception as exc:
            raise OpenAIUnavailableError("The OpenAI SDK is not installed.") from exc
        return OpenAI(api_key=api_key)

    def _result(self, response: Any) -> OpenAIResult:
        content = getattr(response, "output_text", None) or self._extract_text(response) or ""
        usage = getattr(response, "usage", None)
        model = getattr(response, "model", None) or self.model
        return OpenAIResult(
            content=content.strip() or "I could not generate a lesson from this image.",
            response_id=getattr(response, "id", None),
            model=model,
            input_tokens=self._usage_value(usage, "input_tokens"),
            output_tokens=self._usage_value(usage, "output_tokens"),
            total_tokens=self._usage_value(usage, "total_tokens"),
        )

    @staticmethod
    def _usage_value(usage: Any, key: str) -> Optional[int]:
        if usage is None:
            return None
        if isinstance(usage, dict):
            value = usage.get(key)
        else:
            value = getattr(usage, key, None)
        return int(value) if value is not None else None

    @staticmethod
    def _extract_text(response: Any) -> Optional[str]:
        if isinstance(response, dict):
            return response.get("output_text")
        return None

    @staticmethod
    def _is_auth_error(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        return status_code == 401 or exc.__class__.__name__ in {"AuthenticationError", "PermissionDeniedError"}


openai_client = OpenAIClient()
