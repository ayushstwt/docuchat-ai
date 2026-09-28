from sqlalchemy import BigInteger, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.constants.enums import ActivityAction, ActivitySubAction
from app.models.base import BaseModel


class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[ActivityAction] = mapped_column(
        SQLEnum(ActivityAction, name="activity_action_enum"),
        nullable=False,
    )
    sub_action: Mapped[ActivitySubAction] = mapped_column(
        SQLEnum(ActivitySubAction, name="activity_sub_action_enum"),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_activity_logs_user_id_created_on", "user_id", "created_on"),
    )
