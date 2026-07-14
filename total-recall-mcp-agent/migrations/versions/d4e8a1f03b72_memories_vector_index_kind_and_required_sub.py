"""memories vector index kind prefix and required cognito_sub

Revision ID: d4e8a1f03b72
Revises: b7e4f1a29c80
Create Date: 2026-07-14 02:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4e8a1f03b72"
down_revision: str | Sequence[str] | None = "b7e4f1a29c80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        """
        UPDATE memories
        SET cognito_sub = 'local-test-user'
        WHERE cognito_sub IS NULL
        """
    )
    op.execute("ALTER TABLE memories ALTER COLUMN cognito_sub SET NOT NULL")

    op.execute("DROP INDEX IF EXISTS memories_vector_idx")
    op.execute(
        """
        CREATE VECTOR INDEX memories_vector_idx
        ON memories (cognito_sub, kind, embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DROP INDEX IF EXISTS memories_vector_idx")
    op.execute(
        """
        CREATE VECTOR INDEX memories_vector_idx
        ON memories (cognito_sub, embedding vector_cosine_ops)
        """
    )
    op.execute("ALTER TABLE memories ALTER COLUMN cognito_sub DROP NOT NULL")
