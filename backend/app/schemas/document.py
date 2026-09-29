from datetime import datetime
from typing import Optional
from app.constants.enums import DocumentStatus
from app.schemas.common import CamelModel


class DocumentResponse(CamelModel):
    id: int
    title: str
    original_filename: str
    file_size: int
    page_count: Optional[int] = None
    status: DocumentStatus
    error_code: Optional[str] = None
    created_on: datetime
    updated_on: datetime
