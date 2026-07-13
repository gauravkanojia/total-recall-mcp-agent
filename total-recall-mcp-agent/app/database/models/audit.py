"""
Audit log model.
"""

from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.models.base import Base
from app.database.models.base import UUIDMixin
from app.database.models.base import TimestampMixin


class AuditLog(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    """
    MCP execution audit record.
    """

    __tablename__ = "audit_logs"

    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    request_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    cognito_sub: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # created_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     default=lambda: datetime.now(UTC),
    #     nullable=False,
    # )

    # updated_at: Mapped[datetime] = mapped_column(
    #     DateTime(timezone=True),
    #     default=lambda: datetime.now(UTC),
    #     onupdate=lambda: datetime.now(UTC),
    #     nullable=False,
    # )
