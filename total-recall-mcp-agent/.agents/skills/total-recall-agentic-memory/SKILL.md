---
name: total-recall-agentic-memory
description: >-
  Guides development and operations for the Total Recall MCP agent — CockroachDB-backed
  agentic memory with vector search, audit logging, and MCP tools. Use when working on
  this hackathon project, semantic memory (remember_memory/recall_memory), vector indexes,
  CockroachDB Cloud setup, ccloud CLI, or integrating Bedrock embeddings with CockroachDB.
---

# Total Recall MCP — Agentic Memory

This project is an MCP agent where **CockroachDB is the system of record** for agent memory.

## Architecture

| Layer | Role |
|---|---|
| MCP tools | `remember_memory`, `recall_memory`, `get_user`, `health_check` |
| `MCPToolExecutor` | Transaction + `audit_logs` on every tool call |
| `memories` table | `VECTOR(1024)` embeddings + distributed vector index |
| Embeddings | Bedrock Titan v2 (production) or fake provider (local) |

## Schema (CockroachDB)

```sql
-- Semantic memory with distributed vector index
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id STRING(255) NOT NULL,
    kind STRING NOT NULL,
    content STRING NOT NULL,
    metadata JSONB,
    embedding VECTOR(1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE VECTOR INDEX memories_vector_idx
ON memories (principal_id, kind, embedding vector_cosine_ops);
```

Also: `users`, `audit_logs`. Migrations in `migrations/versions/`.

## Project scripts

| Script | Purpose |
|---|---|
| `scripts/ccloud_cluster_info.sh <cluster>` | Cloud cluster metadata via ccloud CLI (`-o json`) |
| `scripts/demo_memory.sh` | Demo remember/recall flow |
| `scripts/seed_memories.py` | Seed sample memories |
| `scripts/install_cockroachdb_skills.sh` | Install upstream CockroachDB Agent Skills |

## MCP configuration

- Local stdio: `app/mcp-dev.json`
- Cloud DB + Cloud MCP: `app/mcp-cloud.example.json`

## When to use upstream CockroachDB skills

Pair this skill with installed skills from [cockroachlabs/cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills):

| Task | Upstream skill |
|---|---|
| SQL / schema / vector DDL | `cockroachdb-sql` |
| Local CockroachDB setup | `setting-up-local-cluster` |
| Cloud cluster health checks | `reviewing-cluster-health` |
| Transaction patterns for tool calls | `designing-application-transactions` |
| Audit logging design | `configuring-audit-logging` |

## Vector memory guidelines

1. Keep `EMBEDDING_DIMENSIONS=1024` aligned with Bedrock Titan v2 and the `VECTOR(1024)` column.
2. Scope recall by `principal_id` — required on every memory row; vector index prefix is `(principal_id, kind)`.
3. Pass `kind` to `recall_memory` when possible — the vector index includes `kind` as a prefix column for filtered recall.
4. Store structured tags in `metadata` JSONB, not in `content`.
5. Run `uv run alembic upgrade head` after pointing `DATABASE_URL` at a new cluster.

## Local dev quick path

```bash
uv sync
docker compose up -d
uv run alembic upgrade head
uv run total-recall-mcp-agent
```

## Cloud path

```bash
export CCLOUD_CLUSTER_NAME=<your-cluster>
./scripts/ccloud_cluster_info.sh
# Set DATABASE_URL in .env, then:
uv run alembic upgrade head
```
