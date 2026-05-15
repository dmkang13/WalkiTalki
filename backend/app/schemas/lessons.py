from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ApiSchema, ChatMessageRead, UsageRead


class LessonSessionRead(ApiSchema):
    id: UUID
    agent_id: UUID
    lesson_markdown: str
    usage: Optional[UsageRead] = None
    messages: List[ChatMessageRead]


class MessageCreate(ApiSchema):
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def content_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message content is required.")
        return value


class MessageCreateRead(ApiSchema):
    message: ChatMessageRead
    usage: Optional[UsageRead] = None
