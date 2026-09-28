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
