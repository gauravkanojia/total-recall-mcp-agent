"""
User DB Model for the MCP Server
"""

from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.models.base import Base
from app.database.models.base import TimestampMixin
from app.database.models.base import UUIDMixin


class User(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    """
    User entity.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default=text("true"),
    )

    cognito_sub: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
