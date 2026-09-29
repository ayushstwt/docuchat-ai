import logging
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ActivityAction, ActivitySubAction, DocumentStatus
from app.constants.error_codes import ErrorCode
from app.exceptions.base import AppException, ConflictException, NotFoundException
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.document_repo import DocumentRepository
from app.schemas.conversation import ConversationResponse, CreateConversationRequest, UpdateConversationRequest
from app.services.activity_service import ActivityService

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.activity_service = ActivityService(db)

    async def create(self, user: User, req: CreateConversationRequest) -> ConversationResponse:
        # Validate that all document IDs belong to user and are in status READY
        first_doc_title = None
        for doc_id in req.document_ids:
            doc = await self.doc_repo.get_owned(doc_id, user.id)
            if not doc:
                raise NotFoundException(ErrorCode.DOCUMENT_NOT_FOUND, doc_id)
            if doc.status != DocumentStatus.READY:
                raise ConflictException(ErrorCode.DOCUMENT_NOT_READY, doc.status.value if hasattr(doc.status, "value") else str(doc.status))
            if first_doc_title is None:
                first_doc_title = doc.title

        title = req.title.strip() if req.title and req.title.strip() else (first_doc_title or "New Conversation")

        try:
            conv, doc_ids = await self.conv_repo.create(
                user_id=user.id,
                title=title[:120],
                document_ids=req.document_ids,
            )
            await self.activity_service.record(
                user_id=user.id,
                action=ActivityAction.CONVERSATION_CREATE,
                sub_action=ActivitySubAction.SUCCESS,
            )
            await self.db.commit()

            return ConversationResponse(
                id=conv.id,
                title=conv.title,
                document_ids=doc_ids,
                created_on=conv.created_on,
                updated_on=conv.updated_on,
            )
        except Exception:
            await self.db.rollback()
            raise

    async def list_conversations(
        self,
        user_id: int,
        page: int = 0,
        size: int = 10,
    ) -> Tuple[List[ConversationResponse], int]:
        items, total = await self.conv_repo.list_owned_paginated(
            user_id=user_id,
            page=page,
            size=size,
        )
        responses = [
            ConversationResponse(
                id=c.id,
                title=c.title,
                document_ids=doc_ids,
                created_on=c.created_on,
                updated_on=c.updated_on,
            )
            for c, doc_ids in items
        ]
        return responses, total

    async def get_conversation(self, conv_id: int, user_id: int) -> ConversationResponse:
        result = await self.conv_repo.get_owned(conv_id, user_id)
        if not result:
            raise NotFoundException(ErrorCode.CONVERSATION_NOT_FOUND, conv_id)
        conv, doc_ids = result
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            document_ids=doc_ids,
            created_on=conv.created_on,
            updated_on=conv.updated_on,
        )

    async def rename_conversation(
        self,
        conv_id: int,
        user_id: int,
        req: UpdateConversationRequest,
    ) -> ConversationResponse:
        conv = await self.conv_repo.update_title(conv_id, user_id, req.title.strip()[:120])
        if not conv:
            raise NotFoundException(ErrorCode.CONVERSATION_NOT_FOUND, conv_id)
        await self.db.commit()
        return await self.get_conversation(conv_id, user_id)

    async def delete_conversation(self, conv_id: int, user_id: int) -> None:
        deleted = await self.conv_repo.soft_delete(conv_id, user_id)
        if not deleted:
            raise NotFoundException(ErrorCode.CONVERSATION_NOT_FOUND, conv_id)
        await self.db.commit()
