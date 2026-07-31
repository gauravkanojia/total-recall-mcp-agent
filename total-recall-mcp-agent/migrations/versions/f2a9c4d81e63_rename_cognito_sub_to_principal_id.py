"""rename cognito_sub to principal_id and add timestamp server defaults

The application always called this value principal_id; the column now says
the same (auth is GitHub-backed bearer tokens, not Cognito). Also gives
users/audit_logs timestamp columns server-side defaults so raw SQL inserts
work without the ORM.

Revision ID: f2a9c4d81e63
Revises: d4e8a1f03b72
Create Date: 2026-07-18 01:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a9c4d81e63"
down_revision: str | Sequence[str] | None = "d4e8a1f03b72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("users", "audit_logs", "memories")


def upgrade() -> None:
    """Upgrade schema."""

    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} RENAME COLUMN cognito_sub TO principal_id")

    # Dependent index / unique-constraint names keep working after a column
    # rename, but rename them too so the schema reads consistently.
    op.execute(
        "ALTER INDEX IF EXISTS ix_memories_cognito_sub RENAME TO ix_memories_principal_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS users_cognito_sub_key RENAME TO users_principal_id_key"
    )

    # memories already has TIMESTAMPTZ defaults from its raw-DDL migration.
    for table in ("users", "audit_logs"):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at SET DEFAULT now()")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN updated_at SET DEFAULT now()")


def downgrade() -> None:
    """Downgrade schema."""

    for table in ("users", "audit_logs"):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at DROP DEFAULT")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN updated_at DROP DEFAULT")

    op.execute(
        "ALTER INDEX IF EXISTS users_principal_id_key RENAME TO users_cognito_sub_key"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_memories_principal_id RENAME TO ix_memories_cognito_sub"
    )

    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} RENAME COLUMN principal_id TO cognito_sub")
