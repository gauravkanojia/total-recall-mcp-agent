"""
Memory DB model for semantic agent memory.
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.database.models.base import Base, TimestampMixin, UUIDMixin


class Memory(UUIDMixin, TimestampMixin, Base):
    """
    Persistent semantic memory stored with a vector embedding.
    """

    __tablename__ = "memories"

    cognito_sub: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    kind: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSIONS),
        nullable=True,
    )
