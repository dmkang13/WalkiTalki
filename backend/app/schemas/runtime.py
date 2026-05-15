from typing import Optional

from pydantic import Field

from app.schemas.common import ApiSchema


class OpenAIKeyValidateRequest(ApiSchema):
    api_key: Optional[str] = Field(default=None, alias="apiKey")


class OpenAIKeyStatus(ApiSchema):
    has_api_key: bool
