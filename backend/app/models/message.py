from typing import Any, Optional
from sqlalchemy import BigInteger, Enum as SQLEnum, ForeignKey, Index, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.constants.enums import MessageRole
from app.models.base import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"

    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole, name="message_role_enum"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    sources: Mapped[Optional[Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    prompt_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    completion_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_messages_conversation_id_created_on", "conversation_id", "created_on"),
    )
