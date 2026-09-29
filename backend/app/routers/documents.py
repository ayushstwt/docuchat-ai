from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import DocumentStatus
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse, PageMetadata, PageParams, respond
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService, process_document

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF document",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc_response = await service.upload(current_user, file)
    # Trigger background ingestion
    background_tasks.add_task(process_document, doc_response.id)

    envelope = ApiResponse.success(
        message="Document uploaded successfully",
        data=doc_response,
    )
    headers = {"Location": f"/api/v1/documents/{doc_response.id}"}
    return respond(envelope, status_code=status.HTTP_201_CREATED, headers=headers)


@router.get(
    "",
    summary="List documents",
)
async def list_documents(
    page_params: PageParams = Depends(),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    items, total = await service.list_documents(
        user_id=current_user.id,
        page=page_params.page,
        size=page_params.size,
        status=status_filter,
    )
    metadata = PageMetadata.of(
        page=page_params.page,
        size=page_params.size,
        total_items=total,
    )
    envelope = ApiResponse.success(
        message="Documents retrieved successfully",
        data=items,
        metadata=metadata,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)


@router.get(
    "/{document_id}",
    summary="Get document details",
)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document(document_id, current_user.id)
    envelope = ApiResponse.success(
        message="Document retrieved successfully",
        data=doc,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)


@router.get(
    "/{document_id}/file",
    summary="Download or preview document PDF file",
)
async def get_document_file(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    file_path, filename = await service.get_document_file_path(document_id, current_user.id)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    await service.delete_document(document_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
