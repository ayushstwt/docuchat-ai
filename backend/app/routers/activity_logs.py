from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse
from app.schemas.common import ApiResponse, PageMetadata, PageParams, respond
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get(
    "",
    summary="List current user's activity logs",
)
async def list_activity_logs(
    page_params: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ActivityService(db)
    items, total = await service.list_logs(
        user_id=current_user.id,
        page=page_params.page,
        size=page_params.size,
    )
    metadata = PageMetadata.of(
        page=page_params.page,
        size=page_params.size,
        total_items=total,
    )
    envelope = ApiResponse.success(
        message="Activity logs retrieved successfully",
        data=items,
        metadata=metadata,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)
