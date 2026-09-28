from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import jwt

from app.constants.error_codes import ErrorCode
from app.core.config import get_settings
from app.exceptions.base import UnauthorizedException

settings = get_settings()
ph = PasswordHasher()
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, Exception):
        return False


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        if payload.get("type") != expected_type:
            raise UnauthorizedException(ErrorCode.TOKEN_INVALID_OR_EXPIRED)
        return payload
    except (jwt.PyJWTError, Exception):
        raise UnauthorizedException(ErrorCode.TOKEN_INVALID_OR_EXPIRED)
