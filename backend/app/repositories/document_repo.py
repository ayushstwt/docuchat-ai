from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import DocumentStatus
from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        title: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        status: DocumentStatus = DocumentStatus.UPLOADED,
    ) -> Document:
        doc = Document(
            user_id=user_id,
            title=title,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            status=status,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def get_by_id(self, doc_id: int) -> Optional[Document]:
        stmt = (
            select(Document)
            .where(
                Document.id == doc_id,
                Document.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_owned(self, doc_id: int, user_id: int) -> Optional[Document]:
        stmt = (
            select(Document)
            .where(
                Document.id == doc_id,
                Document.user_id == user_id,
                Document.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_owned_paginated(
        self,
        user_id: int,
        page: int = 0,
        size: int = 10,
        status: Optional[DocumentStatus] = None,
    ) -> Tuple[List[Document], int]:
        base_filters = [
            Document.user_id == user_id,
            Document.is_deleted.is_(False),
        ]
        if status:
            base_filters.append(Document.status == status)

        # Count total
        count_stmt = select(func.count(Document.id)).where(*base_filters)
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0

        # Query items
        offset_val = (page - 1) * size if page > 0 else 0
        stmt = (
            select(Document)
            .where(*base_filters)
            .order_by(Document.created_on.desc())
            .offset(offset_val)
            .limit(size)
        )
        items_result = await self.db.execute(stmt)
        items = list(items_result.scalars().all())

        return items, total_items

    async def update_status(
        self,
        doc_id: int,
        status: DocumentStatus,
        error_code: Optional[str] = None,
        page_count: Optional[int] = None,
    ) -> None:
        values = {
            "status": status,
            "error_code": error_code,
            "updated_on": datetime.now(timezone.utc),
        }
        if page_count is not None:
            values["page_count"] = page_count

        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(**values)
        )
        await self.db.execute(stmt)

    async def soft_delete(self, doc_id: int, user_id: int) -> bool:
        stmt = (
            update(Document)
            .where(
                Document.id == doc_id,
                Document.user_id == user_id,
                Document.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                updated_on=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
