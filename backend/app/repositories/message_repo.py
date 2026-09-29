from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import MessageRole
from app.models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        sources: Optional[List[dict]] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def list_by_conversation_paginated(
        self,
        conversation_id: int,
        page: int = 0,
        size: int = 20,
    ) -> Tuple[List[Message], int]:
        base_filters = [
            Message.conversation_id == conversation_id,
            Message.is_deleted.is_(False),
        ]

        count_stmt = select(func.count(Message.id)).where(*base_filters)
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0

        # Ordered by created_on ASC
        stmt = (
            select(Message)
            .where(*base_filters)
            .order_by(Message.created_on.asc())
            .offset(page * size)
            .limit(size)
        )
        items_result = await self.db.execute(stmt)
        messages = list(items_result.scalars().all())

        return messages, total_items

    async def get_recent_history(
        self,
        conversation_id: int,
        limit: int = 6,
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted.is_(False),
            )
            .order_by(Message.created_on.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages
