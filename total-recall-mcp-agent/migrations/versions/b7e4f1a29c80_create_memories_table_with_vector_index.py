"""create memories table with vector index

Revision ID: b7e4f1a29c80
Revises: 39d0cad20c36
Create Date: 2026-07-13 13:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e4f1a29c80"
down_revision: str | Sequence[str] | None = "39d0cad20c36"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute(
        """
        CREATE TABLE memories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cognito_sub STRING NOT NULL,
            kind STRING NOT NULL,
            content STRING NOT NULL,
            metadata JSONB,
            embedding VECTOR(1024),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX ix_memories_cognito_sub ON memories (cognito_sub)")
    op.execute("CREATE INDEX ix_memories_kind ON memories (kind)")

    op.execute(
        """
        CREATE VECTOR INDEX memories_vector_idx
        ON memories (cognito_sub, kind, embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("DROP INDEX IF EXISTS memories_vector_idx")
    op.execute("DROP INDEX IF EXISTS ix_memories_kind")
    op.execute("DROP INDEX IF EXISTS ix_memories_cognito_sub")
    op.execute("DROP TABLE IF EXISTS memories")
