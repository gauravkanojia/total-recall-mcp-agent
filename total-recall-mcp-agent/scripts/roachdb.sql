-- Reference schema for total-recall-mcp-agent (matches Alembic migrations).
-- Application code maps principal_id -> cognito_sub column.
-- Source of truth: run `uv run alembic upgrade head` instead of applying this file directly.
--
-- Revisions: 991e2ce09de4 -> 4af598f96850 -> 39d0cad20c36 -> b7e4f1a29c80 -> d4e8a1f03b72

CREATE DATABASE IF NOT EXISTS total_recall_mcp_db;

-- users (991e2ce09de4)
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY,
    email       STRING(320) NOT NULL,
    first_name  STRING(100) NOT NULL,
    last_name   STRING(100) NOT NULL,
    is_active   BOOL NOT NULL DEFAULT true,
    cognito_sub STRING(255),
    created_at  TIMESTAMPTZ NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL,
    UNIQUE (cognito_sub)
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- audit_logs (4af598f96850, 39d0cad20c36)
CREATE TABLE IF NOT EXISTS audit_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name     STRING(100) NOT NULL,
    request_id    STRING(100) NOT NULL,
    cognito_sub   STRING(255),
    status        STRING(50) NOT NULL,
    error_message STRING,
    created_at    TIMESTAMPTZ NOT NULL,
    updated_at    TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_request_id ON audit_logs (request_id);

-- memories (b7e4f1a29c80, d4e8a1f03b72)
CREATE TABLE IF NOT EXISTS memories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cognito_sub STRING(255) NOT NULL,
    kind        STRING(50) NOT NULL,
    content     STRING NOT NULL,
    metadata    JSONB,
    embedding   VECTOR(1024),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_memories_cognito_sub ON memories (cognito_sub);
CREATE INDEX IF NOT EXISTS ix_memories_kind ON memories (kind);

CREATE VECTOR INDEX IF NOT EXISTS memories_vector_idx
ON memories (cognito_sub, kind, embedding vector_cosine_ops);
