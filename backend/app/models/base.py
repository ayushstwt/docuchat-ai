from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger, "postgresql"),
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
