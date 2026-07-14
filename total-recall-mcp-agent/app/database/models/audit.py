"""
Audit log model.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, TimestampMixin, UUIDMixin


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

    principal_id: Mapped[str | None] = mapped_column(
        "cognito_sub",
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
