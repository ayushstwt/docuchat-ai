from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationDocument


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        title: str,
        document_ids: List[int],
    ) -> Tuple[Conversation, List[int]]:
        conv = Conversation(
            user_id=user_id,
            title=title,
        )
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)

        # Associate documents
        conv_docs = [
            ConversationDocument(
                conversation_id=conv.id,
                document_id=doc_id,
            )
            for doc_id in set(document_ids)
        ]
        self.db.add_all(conv_docs)
        await self.db.flush()

        return conv, list(set(document_ids))

    async def get_owned(self, conv_id: int, user_id: int) -> Optional[Tuple[Conversation, List[int]]]:
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conv_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            )
        )
        result = await self.db.execute(stmt)
        conv = result.scalar_one_or_none()
        if not conv:
            return None

        # Fetch associated document ids
        docs_stmt = (
            select(ConversationDocument.document_id)
            .where(
                ConversationDocument.conversation_id == conv.id,
                ConversationDocument.is_deleted.is_(False),
            )
        )
        doc_ids_result = await self.db.execute(docs_stmt)
        doc_ids = list(doc_ids_result.scalars().all())

        return conv, doc_ids

    async def list_owned_paginated(
        self,
        user_id: int,
        page: int = 0,
        size: int = 10,
    ) -> Tuple[List[Tuple[Conversation, List[int]]], int]:
        base_filters = [
            Conversation.user_id == user_id,
            Conversation.is_deleted.is_(False),
        ]

        # Total count
        count_stmt = select(func.count(Conversation.id)).where(*base_filters)
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0

        # Items ordered by created_on DESC
        offset_val = (page - 1) * size if page > 0 else 0
        stmt = (
            select(Conversation)
            .where(*base_filters)
            .order_by(Conversation.created_on.desc())
            .offset(offset_val)
            .limit(size)
        )
        items_result = await self.db.execute(stmt)
        conversations = list(items_result.scalars().all())

        results: List[Tuple[Conversation, List[int]]] = []
        if conversations:
            conv_ids = [c.id for c in conversations]
            docs_stmt = (
                select(ConversationDocument.conversation_id, ConversationDocument.document_id)
                .where(
                    ConversationDocument.conversation_id.in_(conv_ids),
                    ConversationDocument.is_deleted.is_(False),
                )
            )
            doc_rows = await self.db.execute(docs_stmt)
            doc_map: dict[int, list[int]] = {}
            for cid, did in doc_rows.all():
                doc_map.setdefault(cid, []).append(did)

            for c in conversations:
                results.append((c, doc_map.get(c.id, [])))

        return results, total_items

    async def update_title(self, conv_id: int, user_id: int, title: str) -> Optional[Conversation]:
        stmt = (
            update(Conversation)
            .where(
                Conversation.id == conv_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            )
            .values(
                title=title,
                updated_on=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        if result.rowcount > 0:
            return (await self.get_owned(conv_id, user_id))[0]
        return None

    async def soft_delete(self, conv_id: int, user_id: int) -> bool:
        stmt = (
            update(Conversation)
            .where(
                Conversation.id == conv_id,
                Conversation.user_id == user_id,
                Conversation.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                updated_on=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        if result.rowcount > 0:
            # Soft delete conversation_documents
            await self.db.execute(
                update(ConversationDocument)
                .where(ConversationDocument.conversation_id == conv_id)
                .values(
                    is_deleted=True,
                    updated_on=datetime.now(timezone.utc),
                )
            )
            return True
        return False
