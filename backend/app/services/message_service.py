import json
import logging
from typing import AsyncGenerator, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ActivityAction, ActivitySubAction, MessageRole
from app.constants.error_codes import ErrorCode
from app.exceptions.base import AppException, NotFoundException
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.common import ApiResponse
from app.schemas.message import MessageResponse
from app.services.activity_service import ActivityService
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_repo = MessageRepository(db)
        self.conv_repo = ConversationRepository(db)
        self.activity_service = ActivityService(db)
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService(db)
        self.chat_service = ChatService()

    async def list_messages(
        self,
        conversation_id: int,
        user_id: int,
        page: int = 0,
        size: int = 20,
    ) -> Tuple[List[MessageResponse], int]:
        # Validate conversation ownership
        conv = await self.conv_repo.get_owned(conversation_id, user_id)
        if not conv:
            raise NotFoundException(ErrorCode.CONVERSATION_NOT_FOUND, conversation_id)

        items, total = await self.message_repo.list_by_conversation_paginated(
            conversation_id=conversation_id,
            page=page,
            size=size,
        )
        responses = [
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_on=m.created_on,
            )
            for m in items
        ]
        return responses, total

    async def validate_access(self, user: User, conversation_id: int) -> Tuple[int, List[int]]:
        """
        Validates conversation ownership and returns (conversation_id, document_ids).
        Raises NotFoundException(ErrorCode.CONVERSATION_NOT_FOUND) if not found or not owned.
        """
        conv_result = await self.conv_repo.get_owned(conversation_id, user.id)
        if not conv_result:
            raise NotFoundException(ErrorCode.CONVERSATION_NOT_FOUND, conversation_id)
        conv, doc_ids = conv_result
        return conv.id, doc_ids

    async def send_message_stream(
        self,
        user: User,
        conversation_id: int,
        document_ids: List[int],
        content: str,
    ) -> AsyncGenerator[str, None]:
        """
        SSE stream generator:
          a. Save user message.
          b. Embed question + retrieve chunks -> yield 'event: sources'
          c. Stream answer tokens -> yield 'event: token'
          d. Save assistant message -> yield 'event: done' with full ApiResponse envelope.
          e. On exception: record CHAT_MESSAGE FAILED -> yield 'event: error' with error envelope.
        """
        # Step a: Save USER message
        try:
            user_msg = await self.message_repo.create(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=content,
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
            err_envelope = ApiResponse.error(
                error_code=ErrorCode.INTERNAL_ERROR.code,
                message=ErrorCode.INTERNAL_ERROR.message_template,
                path=f"/api/v1/conversations/{conversation_id}/messages",
            )
            yield f"event: error\ndata: {err_envelope.model_dump_json(by_alias=True, exclude_none=True)}\n\n"
            return

        # Fetch recent conversation history for chat context (last 6 messages before current)
        history_records = await self.message_repo.get_recent_history(conversation_id, limit=6)
        history = [
            {"role": "user" if m.role == MessageRole.USER else "assistant", "content": m.content}
            for m in history_records
            if m.id != user_msg.id
        ]

        full_assistant_text = []
        sources = []
        prompt_tokens = 0
        completion_tokens = 0

        try:
            # Step b: Embed question and retrieve chunks
            query_embedding = await self.embedding_service.embed_query(content)
            chunks = await self.retrieval_service.search(
                user_id=user.id,
                document_ids=document_ids,
                query_embedding=query_embedding,
                top_k=6,
                min_similarity=0.2,
            )
            sources = self.chat_service.build_sources(chunks)

            # Yield sources event
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

            # Step c: Stream answer tokens
            async for item in self.chat_service.stream_answer(
                question=content,
                chunks=chunks,
                history=history,
            ):
                if item.get("type") == "token":
                    delta_text = item.get("text", "")
                    full_assistant_text.append(delta_text)
                    token_payload = json.dumps({"text": delta_text})
                    yield f"event: token\ndata: {token_payload}\n\n"
                elif item.get("type") == "usage":
                    prompt_tokens = item.get("prompt_tokens", 0)
                    completion_tokens = item.get("completion_tokens", 0)

            assistant_content = "".join(full_assistant_text).strip()

            # Step d: Save ASSISTANT message
            asst_msg = await self.message_repo.create(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                sources=sources,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            await self.activity_service.record(
                user_id=user.id,
                action=ActivityAction.CHAT_MESSAGE,
                sub_action=ActivitySubAction.SUCCESS,
            )
            await self.db.commit()

            msg_response = MessageResponse(
                id=asst_msg.id,
                role=asst_msg.role,
                content=asst_msg.content,
                sources=asst_msg.sources,
                created_on=asst_msg.created_on,
            )
            done_envelope = ApiResponse.success(
                message="Message sent successfully",
                data=msg_response,
            )
            yield f"event: done\ndata: {done_envelope.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

        except AppException as ae:
            logger.warning(f"Chat stream AppException: {ae.error.code} - {ae.message}")
            await self._record_failure(user.id)
            err_envelope = ApiResponse.error(
                error_code=ae.error.code,
                message=ae.message,
                path=f"/api/v1/conversations/{conversation_id}/messages",
            )
            yield f"event: error\ndata: {err_envelope.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

        except Exception as ex:
            logger.error(f"Chat stream unexpected error: {ex}", exc_info=True)
            await self._record_failure(user.id)
            err_envelope = ApiResponse.error(
                error_code=ErrorCode.INTERNAL_ERROR.code,
                message=ErrorCode.INTERNAL_ERROR.message_template,
                path=f"/api/v1/conversations/{conversation_id}/messages",
            )
            yield f"event: error\ndata: {err_envelope.model_dump_json(by_alias=True, exclude_none=True)}\n\n"

    async def _record_failure(self, user_id: int):
        try:
            await self.activity_service.record(
                user_id=user_id,
                action=ActivityAction.CHAT_MESSAGE,
                sub_action=ActivitySubAction.FAILED,
            )
            await self.db.commit()
        except Exception:
            pass
