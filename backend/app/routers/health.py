from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse, respond

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Health Check")
async def health_check(db: AsyncSession = Depends(get_db)) -> Any:
    db_status = "up"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    payload = {
        "app": "DocuChat AI",
        "database": db_status,
    }
    envelope = ApiResponse.success(
        message="System status",
        data=payload,
    )
    return respond(envelope)
