from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ApiSchema


class AgentCreate(ApiSchema):
    name: str = Field(..., min_length=1, max_length=80)
    target_language: str = Field(..., alias="targetLanguage", min_length=1, max_length=80)
    native_language: Optional[str] = Field(default=None, alias="nativeLanguage", max_length=80)
    custom_instructions: Optional[str] = Field(default=None, alias="customInstructions", max_length=1000)

    @field_validator("name", "target_language")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field is required.")
        return value

    @field_validator("native_language", "custom_instructions")
    @classmethod
    def optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class AgentUpdate(ApiSchema):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    target_language: Optional[str] = Field(default=None, alias="targetLanguage", min_length=1, max_length=80)
    native_language: Optional[str] = Field(default=None, alias="nativeLanguage", max_length=80)
    custom_instructions: Optional[str] = Field(default=None, alias="customInstructions", max_length=1000)

    @field_validator("name", "target_language")
    @classmethod
    def required_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty.")
        return value

    @field_validator("native_language", "custom_instructions")
    @classmethod
    def optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class AgentRead(ApiSchema):
    id: UUID
    name: str
    target_language: str
    native_language: Optional[str] = None
    custom_instructions: Optional[str] = None
    status: str


class SharedAgentRead(AgentRead):
    share_slug: str


class SharedAgentListRead(ApiSchema):
    agents: List[SharedAgentRead]


class AgentPublishRead(ApiSchema):
    id: UUID
    status: str
    share_slug: str
    share_url: str
