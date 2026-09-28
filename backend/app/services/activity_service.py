from sqlalchemy.ext.asyncio import AsyncSession
from app.constants.enums import ActivityAction, ActivitySubAction
from app.repositories.activity_repo import ActivityRepository


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
