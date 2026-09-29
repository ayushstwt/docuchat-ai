from datetime import datetime
from typing import Any, List, Optional
from pydantic import Field, field_validator
from app.constants.enums import MessageRole
from app.schemas.common import CamelModel


class SendMessageRequest(CamelModel):
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def trim_content(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message content cannot be empty or whitespace only")
        return trimmed


class MessageResponse(CamelModel):
    id: int
    role: MessageRole
    content: str
    sources: Optional[List[dict]] = None
    created_on: datetime
