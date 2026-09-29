from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, limiter
from app.models.user import User
from app.schemas.common import ApiResponse, PageMetadata, PageParams, respond
from app.schemas.conversation import ConversationResponse, CreateConversationRequest, UpdateConversationRequest
from app.schemas.message import MessageResponse, SendMessageRequest
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation",
)
async def create_conversation(
    req: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    conv_response = await service.create(current_user, req)
    envelope = ApiResponse.success(
        message="Conversation created successfully",
        data=conv_response,
    )
    headers = {"Location": f"/api/v1/conversations/{conv_response.id}"}
    return respond(envelope, status_code=status.HTTP_201_CREATED, headers=headers)


@router.get(
    "",
    summary="List conversations",
)
async def list_conversations(
    page_params: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    items, total = await service.list_conversations(
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
        message="Conversations retrieved successfully",
        data=items,
        metadata=metadata,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)


@router.get(
    "/{conversation_id}",
    summary="Get conversation details",
)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    conv_response = await service.get_conversation(conversation_id, current_user.id)
    envelope = ApiResponse.success(
        message="Conversation retrieved successfully",
        data=conv_response,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)


@router.patch(
    "/{conversation_id}",
    summary="Rename conversation",
)
async def rename_conversation(
    conversation_id: int,
    req: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    conv_response = await service.rename_conversation(conversation_id, current_user.id, req)
    envelope = ApiResponse.success(
        message="Conversation updated successfully",
        data=conv_response,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ConversationService(db)
    await service.delete_conversation(conversation_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{conversation_id}/messages",
    summary="List messages in a conversation",
)
async def list_messages(
    conversation_id: int,
    page_params: PageParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    items, total = await service.list_messages(
        conversation_id=conversation_id,
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
        message="Messages retrieved successfully",
        data=items,
        metadata=metadata,
    )
    return respond(envelope, status_code=status.HTTP_200_OK)


@router.post(
    "/{conversation_id}/messages",
    summary="Send message and stream response tokens via SSE",
)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    conversation_id: int,
    req: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    # 1. Validate ownership & readiness before opening the stream
    conv_id, doc_ids = await service.validate_access(current_user, conversation_id)

    # 2. Return SSE streaming response with required headers
    async def sse_event_generator():
        async for chunk in service.send_message_stream(
            user=current_user,
            conversation_id=conv_id,
            document_ids=doc_ids,
            content=req.content,
        ):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
