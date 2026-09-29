from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.schemas.common import CamelModel


class CreateConversationRequest(CamelModel):
    document_ids: List[int] = Field(..., min_length=1, alias="documentIds")
    title: Optional[str] = Field(None, max_length=120)


class UpdateConversationRequest(CamelModel):
    title: str = Field(..., min_length=1, max_length=120)


class ConversationResponse(CamelModel):
    id: int
    title: str
    document_ids: List[int] = Field(default_factory=list, alias="documentIds")
    created_on: datetime
    updated_on: datetime
