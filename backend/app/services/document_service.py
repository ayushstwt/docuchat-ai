import logging
import os
import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ActivityAction, ActivitySubAction, DocumentStatus
from app.constants.error_codes import ErrorCode
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.exceptions.base import AppException, NotFoundException
from app.models.document import Document
from app.models.user import User
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.schemas.document import DocumentResponse
from app.services.activity_service import ActivityService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import PdfService

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)
        self.activity_service = ActivityService(db)

    async def upload(self, user: User, file: UploadFile) -> DocumentResponse:
        # 1. Validate content-type
        content_type = file.content_type or ""
        if content_type.lower() != "application/pdf":
            raise AppException(ErrorCode.FILE_NOT_PDF)

        # 2. Check magic bytes (%PDF-) by reading the first 5 bytes
        first_bytes = await file.read(5)
        await file.seek(0)
        if not first_bytes.startswith(b"%PDF-"):
            raise AppException(ErrorCode.FILE_NOT_PDF)

        # 3. Stream to disk under UPLOAD_DIR/<user_id>/<uuid>.pdf enforcing MAX_UPLOAD_MB
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user.id))
        os.makedirs(user_upload_dir, exist_ok=True)

        stored_filename = f"{uuid.uuid4().hex}.pdf"
        target_path = os.path.join(user_upload_dir, stored_filename)

        total_bytes = 0
        try:
            with open(target_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 64)  # 64KB chunks
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise AppException(ErrorCode.FILE_TOO_LARGE, settings.MAX_UPLOAD_MB)
                    buffer.write(chunk)
        except AppException:
            # Clean up partial file on validation failure
            if os.path.exists(target_path):
                os.remove(target_path)
            raise
        except Exception as e:
            if os.path.exists(target_path):
                os.remove(target_path)
            logger.error(f"Failed to stream upload to disk: {e}")
            raise AppException(ErrorCode.INTERNAL_ERROR) from e

        # 4. Create Document record in DB
        original_filename = file.filename or "uploaded.pdf"
        # Use filename as default title (without .pdf if applicable)
        title = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename

        try:
            doc = await self.doc_repo.create(
                user_id=user.id,
                title=title,
                original_filename=original_filename,
                file_path=target_path,
                file_size=total_bytes,
                status=DocumentStatus.UPLOADED,
            )
            await self.activity_service.record(
                user_id=user.id,
                action=ActivityAction.DOCUMENT_UPLOAD,
                sub_action=ActivitySubAction.SUCCESS,
            )
            await self.db.commit()

            return DocumentResponse(
                id=doc.id,
                title=doc.title,
                original_filename=doc.original_filename,
                file_size=doc.file_size,
                page_count=doc.page_count,
                status=doc.status,
                error_code=doc.error_code,
                created_on=doc.created_on,
                updated_on=doc.updated_on,
            )
        except Exception:
            await self.db.rollback()
            if os.path.exists(target_path):
                os.remove(target_path)
            raise

    async def list_documents(
        self,
        user_id: int,
        page: int = 0,
        size: int = 10,
        status: Optional[DocumentStatus] = None,
    ) -> Tuple[List[DocumentResponse], int]:
        items, total = await self.doc_repo.list_owned_paginated(
            user_id=user_id,
            page=page,
            size=size,
            status=status,
        )
        responses = [
            DocumentResponse(
                id=d.id,
                title=d.title,
                original_filename=d.original_filename,
                file_size=d.file_size,
                page_count=d.page_count,
                status=d.status,
                error_code=d.error_code,
                created_on=d.created_on,
                updated_on=d.updated_on,
            )
            for d in items
        ]
        return responses, total

    async def get_document(self, doc_id: int, user_id: int) -> DocumentResponse:
        doc = await self.doc_repo.get_owned(doc_id, user_id)
        if not doc:
            raise NotFoundException(ErrorCode.DOCUMENT_NOT_FOUND, doc_id)

        return DocumentResponse(
            id=doc.id,
            title=doc.title,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            page_count=doc.page_count,
            status=doc.status,
            error_code=doc.error_code,
            created_on=doc.created_on,
            updated_on=doc.updated_on,
        )

    async def get_document_file_path(self, doc_id: int, user_id: int) -> Tuple[str, str]:
        """
        Returns (file_path, original_filename) for the owner.
        """
        doc = await self.doc_repo.get_owned(doc_id, user_id)
        if not doc:
            raise NotFoundException(ErrorCode.DOCUMENT_NOT_FOUND, doc_id)
        if not os.path.exists(doc.file_path):
            raise NotFoundException(ErrorCode.DOCUMENT_NOT_FOUND, doc_id)
        return doc.file_path, doc.original_filename

    async def delete_document(self, doc_id: int, user_id: int) -> None:
        doc = await self.doc_repo.get_owned(doc_id, user_id)
        if not doc:
            raise NotFoundException(ErrorCode.DOCUMENT_NOT_FOUND, doc_id)

        try:
            # Soft delete document
            await self.doc_repo.soft_delete(doc_id, user_id)
            # Soft delete chunks
            await self.chunk_repo.soft_delete_by_document_id(doc_id, user_id)
            # Record activity log
            await self.activity_service.record(
                user_id=user_id,
                action=ActivityAction.DOCUMENT_DELETE,
                sub_action=ActivitySubAction.SUCCESS,
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise


async def process_document(document_id: int, session: Optional[AsyncSession] = None) -> None:
    """
    Runs as a FastAPI BackgroundTask with its OWN async database session (or provided session).
    Pipeline:
      status=PROCESSING -> extract -> chunk -> embed -> insert chunks -> page_count + status=READY.
    On failure:
      status=FAILED with error_code (E012/E014/E999).
    Idempotent: deletes old chunks first.
    """
    pdf_service = PdfService()
    embedding_service = EmbeddingService()

    async def _run_with_session(db_session: AsyncSession):
        doc_repo = DocumentRepository(db_session)
        chunk_repo = ChunkRepository(db_session)

        try:
            doc = await doc_repo.get_by_id(document_id)
            if not doc:
                logger.error(f"process_document: Document with id {document_id} not found")
                return

            # Set status to PROCESSING
            await doc_repo.update_status(document_id, DocumentStatus.PROCESSING)
            await db_session.commit()

            # Idempotency: remove any existing chunks for this document
            await chunk_repo.delete_by_document_id(document_id)
            await db_session.commit()

            # Extract pages
            pages = pdf_service.extract_pages(doc.file_path)
            page_count = len(pages)

            # Chunk pages
            chunks = pdf_service.chunk_pages(pages)
            if not chunks:
                # In case no chunks were produced despite non-empty text check
                raise AppException(ErrorCode.PDF_NO_TEXT)

            # Embed chunks
            texts_to_embed = [c["content"] for c in chunks]
            embeddings = await embedding_service.embed_texts(texts_to_embed)

            # Prepare chunk records
            chunks_to_insert = []
            for chunk_data, emb in zip(chunks, embeddings):
                chunks_to_insert.append({
                    "document_id": doc.id,
                    "user_id": doc.user_id,
                    "chunk_index": chunk_data["chunk_index"],
                    "page_number": chunk_data["page_number"],
                    "content": chunk_data["content"],
                    "token_count": chunk_data["token_count"],
                    "embedding": emb,
                })

            # Bulk insert chunks
            await chunk_repo.bulk_insert(chunks_to_insert)

            # Update document to READY with page_count
            await doc_repo.update_status(
                doc_id=doc.id,
                status=DocumentStatus.READY,
                page_count=page_count,
            )
            await db_session.commit()
            logger.info(f"Document {document_id} successfully processed: {len(chunks_to_insert)} chunks created")

        except AppException as ae:
            await db_session.rollback()
            err_code = ae.error.code
            logger.warning(f"Processing document {document_id} failed with AppException: {err_code} - {ae.message}")
            try:
                await doc_repo.update_status(
                    doc_id=document_id,
                    status=DocumentStatus.FAILED,
                    error_code=err_code,
                )
                await db_session.commit()
            except Exception as update_err:
                logger.error(f"Failed to set status FAILED for document {document_id}: {update_err}")

        except Exception as ex:
            await db_session.rollback()
            logger.error(f"Processing document {document_id} failed unexpectedly: {ex}", exc_info=True)
            try:
                await doc_repo.update_status(
                    doc_id=document_id,
                    status=DocumentStatus.FAILED,
                    error_code=ErrorCode.INTERNAL_ERROR.code,
                )
                await db_session.commit()
            except Exception as update_err:
                logger.error(f"Failed to set status FAILED for document {document_id}: {update_err}")

    if session is not None:
        await _run_with_session(session)
    else:
        async with AsyncSessionLocal() as session_ctx:
            await _run_with_session(session_ctx)
