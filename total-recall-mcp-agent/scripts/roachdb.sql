-- This is dummy setup database for testing the cluster
CREATE DATABASE bank;
CREATE TABLE bank.accounts (id INT PRIMARY KEY, balance DECIMAL);
INSERT INTO bank.accounts VALUES (1, 1000.50);
SELECT * FROM bank.accounts;


-- This is actual database setup for the MCP Server
CREATE DATABASE total_recall_mcp_db;
-- CREATE TABLE total_recall_mcp_db.users (id INT PRIMARY KEY, balance DECIMAL);
CREATE TABLE memories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    session_id  UUID,                          -- conversation grouping
    memory_type VARCHAR(50),                   -- 'fact', 'episode', 'task', 'preference'
    content     TEXT NOT NULL,
    embedding   VECTOR(1536),                  -- CockroachDB vector indexing
    metadata    JSONB,
    importance  FLOAT DEFAULT 0.5,
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON memories (user_id, session_id, memory_type);
