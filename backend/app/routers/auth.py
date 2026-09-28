from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.common import ApiResponse, respond
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Validation error (weak password, invalid email)"},
        409: {"description": "Email already exists (E006)"},
    },
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = AuthService(db)
    user_dto = await service.register(body)
    return respond(
        ApiResponse.success(
            message="User registered successfully",
            data=user_dto,
        ),
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/api/v1/users/{user_dto.id}"},
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate and get tokens",
    responses={
        200: {"description": "Authentication successful"},
        401: {"description": "Invalid email or password (E007)"},
    },
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = AuthService(db)
    tokens = await service.login(body)
    return respond(
        ApiResponse.success(
            message="Login successful",
            data=tokens,
        )
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Token invalid or expired (E008)"},
    },
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = AuthService(db)
    tokens = await service.refresh(body)
    return respond(
        ApiResponse.success(
            message="Token refreshed successfully",
            data=tokens,
        )
    )


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Token invalid or expired (E008)"},
    },
)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = AuthService(db)
    user_dto = await service.get_me(current_user)
    return respond(
        ApiResponse.success(
            message="User profile retrieved",
            data=user_dto,
        )
    )
