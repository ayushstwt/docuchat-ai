from typing import List, Optional
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.config import get_settings
from app.models.base import BaseModel

settings = get_settings()


class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"

    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        JSON,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_document_chunks_user_id_document_id", "user_id", "document_id"),
    )

