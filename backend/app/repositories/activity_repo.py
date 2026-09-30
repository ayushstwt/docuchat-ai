from typing import List, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.constants.enums import ActivityAction, ActivitySubAction
from app.models.activity_log import ActivityLog


class ActivityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        action: ActivityAction,
        sub_action: ActivitySubAction,
    ) -> ActivityLog:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            sub_action=sub_action,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_by_user_paginated(
        self,
        user_id: int,
        page: int = 0,
        size: int = 10,
    ) -> Tuple[List[ActivityLog], int]:
        base_filters = [
            ActivityLog.user_id == user_id,
            ActivityLog.is_deleted.is_(False),
        ]

        count_stmt = select(func.count(ActivityLog.id)).where(*base_filters)
        total_result = await self.db.execute(count_stmt)
        total_items = total_result.scalar() or 0

        offset_val = (page - 1) * size if page > 0 else 0
        stmt = (
            select(ActivityLog)
            .where(*base_filters)
            .order_by(ActivityLog.created_on.desc())
            .offset(offset_val)
            .limit(size)
        )
        items_result = await self.db.execute(stmt)
        items = list(items_result.scalars().all())

        return items, total_items
