from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .where(
                User.id == user_id,
                User.is_deleted.is_(False),
                User.is_active.is_(True),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .where(
                User.email == email.lower().strip(),
                User.is_deleted.is_(False),
                User.is_active.is_(True),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, full_name: str) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name.strip(),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
