from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.constants.enums import ActivityAction, ActivitySubAction
from app.models.activity_log import ActivityLog
from app.repositories.activity_repo import ActivityRepository
from app.schemas.activity_log import ActivityLogResponse


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ActivityRepository(db)

    async def record(
        self,
        user_id: int,
        action: ActivityAction,
        sub_action: ActivitySubAction,
    ) -> None:
        if user_id is None:
            return
        await self.repo.create(user_id=user_id, action=action, sub_action=sub_action)

    async def list_logs(
        self,
        user_id: int,
        page: int = 0,
        size: int = 10,
    ) -> Tuple[List[ActivityLogResponse], int]:
        items, total = await self.repo.list_by_user_paginated(
            user_id=user_id,
            page=page,
            size=size,
        )
        responses = [
            ActivityLogResponse(
                id=log.id,
                action=log.action,
                sub_action=log.sub_action,
                created_on=log.created_on,
            )
            for log in items
        ]
        return responses, total
