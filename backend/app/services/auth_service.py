from sqlalchemy.ext.asyncio import AsyncSession
from app.constants.enums import ActivityAction, ActivitySubAction
from app.constants.error_codes import ErrorCode
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions.base import ConflictException, UnauthorizedException
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.activity_service import ActivityService

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.activity_service = ActivityService(db)

    async def register(self, req: RegisterRequest) -> UserResponse:
        existing_user = await self.user_repo.get_by_email(req.email)
        if existing_user:
            raise ConflictException(ErrorCode.EMAIL_ALREADY_EXISTS, req.email)

        pwd_hash = hash_password(req.password)
        try:
            user = await self.user_repo.create(
                email=req.email,
                password_hash=pwd_hash,
                full_name=req.full_name,
            )
            await self.activity_service.record(
                user_id=user.id,
                action=ActivityAction.REGISTER,
                sub_action=ActivitySubAction.SUCCESS,
            )
            await self.db.commit()
            return UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                created_on=user.created_on,
            )
        except Exception:
            await self.db.rollback()
            raise

    async def login(self, req: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.password_hash):
            if user:
                await self.activity_service.record(
                    user_id=user.id,
                    action=ActivityAction.LOGIN,
                    sub_action=ActivitySubAction.FAILED,
                )
                await self.db.commit()
            raise UnauthorizedException(ErrorCode.INVALID_CREDENTIALS)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        await self.activity_service.record(
            user_id=user.id,
            action=ActivityAction.LOGIN,
            sub_action=ActivitySubAction.SUCCESS,
        )
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_MINUTES * 60,
        )

    async def refresh(self, req: RefreshRequest) -> TokenResponse:
        payload = decode_token(req.refresh_token, expected_type="refresh")
        user_id = int(payload.get("sub", 0))

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException(ErrorCode.TOKEN_INVALID_OR_EXPIRED)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_MINUTES * 60,
        )

    async def get_me(self, current_user: User) -> UserResponse:
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            created_on=current_user.created_on,
        )
