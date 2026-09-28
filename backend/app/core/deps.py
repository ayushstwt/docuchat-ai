from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.error_codes import ErrorCode
from app.core.database import get_db
from app.core.security import decode_token
from app.exceptions.base import UnauthorizedException
from app.models.user import User
from app.repositories.user_repo import UserRepository

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(ErrorCode.TOKEN_INVALID_OR_EXPIRED)

    token = credentials.credentials
    payload = decode_token(token, expected_type="access")
    try:
        user_id = int(payload.get("sub", 0))
    except (ValueError, TypeError):
        raise UnauthorizedException(ErrorCode.TOKEN_INVALID_OR_EXPIRED)

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(ErrorCode.TOKEN_INVALID_OR_EXPIRED)

    return user
