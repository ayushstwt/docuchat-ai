from datetime import datetime, timezone
from typing import List
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_insert(self, chunks_data: List[dict]) -> None:
        if not chunks_data:
            return
        chunks = [
            DocumentChunk(
                document_id=c["document_id"],
                user_id=c["user_id"],
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                content=c["content"],
                token_count=c["token_count"],
                embedding=c.get("embedding"),
            )
            for c in chunks_data
        ]
        self.db.add_all(chunks)
        await self.db.flush()

    async def delete_by_document_id(self, document_id: int) -> int:
        """
        Hard deletes or purges chunks for a given document (e.g. for idempotency re-processing).
        """
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def soft_delete_by_document_id(self, document_id: int, user_id: int) -> int:
        """
        Soft deletes chunks when a document is soft-deleted, explicitly setting updated_on.
        """
        stmt = (
            update(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.user_id == user_id,
                DocumentChunk.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                updated_on=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def get_by_document_id(self, document_id: int, user_id: int) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.user_id == user_id,
                DocumentChunk.is_deleted.is_(False),
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
