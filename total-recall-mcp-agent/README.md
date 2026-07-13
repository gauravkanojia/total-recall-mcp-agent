# cockroachdb-aws-hackathon-aug-2026
Codebase for CockroachDB × AWS Hackathon – Build the Future of Agentic Memory (the “Hackathon”): https://cockroachdb-ai.devpost.com

## Overview

`total-recall-mcp` is an MCP (Model Context Protocol) agent that uses CockroachDB
as its persistent memory layer: every tool call is executed inside a database
transaction and written to an `audit_logs` table, giving the agent a durable,
queryable record of what it did, when, and for whom.

The same set of MCP tools is served through two entry points that share one
bootstrap path (`app/bootstrap.py`), so they can never drift out of sync:

- **`app/cli.py`** – a standalone stdio process for local MCP clients
  (Cursor, Claude Desktop, etc.).
- **`app/main.py`** – a FastAPI/ASGI app that exposes the same tools over
  Streamable HTTP (`/mcp`) for containerized deployments (Docker/ECS on AWS).

### Project Structure

```bash
.
├── app
│   ├── __init__.py
│   ├── auth
│   │   └── mcp_auth.py         # MCP token/principal validation (Cognito JWT, to be wired up)
│   ├── bootstrap.py            # Registers MCP tools once; shared by cli.py and main.py
│   ├── cli.py                  # stdio entry point (uv run total-recall-mcp)
│   ├── clients
│   │   ├── aws.py              # Bedrock runtime client factory
│   │   └── embeddings.py       # Fake + Bedrock embedding providers
│   ├── core
│   │   ├── config.py           # Settings (env-driven)
│   │   └── logging.py          # structlog setup
│   ├── database
│   │   ├── database.py         # Async SQLAlchemy engine (CockroachDB)
│   │   ├── models/              # ORM models: User, AuditLog, Memory
│   │   └── session.py          # Session factory / context manager
│   ├── main.py                 # ASGI entry point (Streamable HTTP, for Docker/ECS)
│   ├── mcp
│   │   ├── bridge.py           # Exposes internal tools as @mcp_server.tool()
│   │   ├── context.py          # Per-request MCPContext (db session, request id, identity)
│   │   ├── context_manager.py  # contextvar helpers for MCPContext
│   │   ├── executor.py         # Runs a tool inside a DB transaction + writes an audit row
│   │   ├── middleware.py       # Builds an MCPContext per tool call
│   │   ├── registry.py         # Registers internal tool handlers with the executor
│   │   └── server.py           # FastMCP server instance
│   ├── repositories/           # DB access: UserRepository, AuditRepository, MemoryRepository
│   ├── schemas/                # Pydantic I/O schemas
│   ├── services/                # Business logic (UserService, MemoryService, ...)
│   └── tools/                  # Tool handlers: health, users, memory
├── docker-compose.yml           # Local single-node CockroachDB
├── Dockerfile
├── LICENSE
├── migrations/                  # Alembic migrations
├── pyproject.toml
├── README.md
├── scripts/
│   └── seed.py                 # Seeds a test user
├── terraform/                   # AWS deployment (ECS, network, IAM, secrets)
└── tests/
```

> Note: `app/dependencies/`, `app/middleware/`, and
> `app/auth/{cognito,dependencies,jwt}.py` currently exist as empty
> placeholders for future work (Cognito auth wiring, request-id/logging
> middleware, DI helpers). They aren't imported anywhere yet.

### Semantic memory (CockroachDB Vector Indexing)

The agent stores long-term semantic memory in a `memories` table backed by
CockroachDB's native `VECTOR` type and a **Distributed Vector Index**
(`memories_vector_idx` with `cognito_sub` as a prefix column for per-user search).

**MCP tools:**
- `remember_memory(content, kind="fact", metadata=None)` — embed and persist a memory
- `recall_memory(query, kind=None, limit=5)` — cosine-similarity search over stored memories

**Embedding providers** (configured via `.env`):
- `EMBEDDING_PROVIDER=fake` — deterministic local embeddings (default, no AWS needed)
- `EMBEDDING_PROVIDER=bedrock` — Amazon Titan Text Embeddings V2 via Bedrock Runtime

```env
EMBEDDING_PROVIDER=fake
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024
```

For production on AWS, set `EMBEDDING_PROVIDER=bedrock` and ensure the ECS task
role has `bedrock:InvokeModel` permission for `amazon.titan-embed-text-v2:0`.

### How to run the MCP server

```bash
cd total-recall-mcp-agent

# 1. Start a local CockroachDB node
docker compose up -d

# 2. Copy the example env and adjust as needed
cp app/.env.example .env

# 3. Sync dependencies
uv sync

# 4. Apply migrations
uv run alembic upgrade head

# 5a. Run as a local stdio MCP server (for Cursor / Claude Desktop)
uv run total-recall-mcp
# equivalent to: uv run python -m app.cli

# 5b. ...or run as an HTTP service (what the Dockerfile/ECS deployment uses)
uv run uvicorn app.main:app --host 0.0.0.0 --port 4646
# MCP endpoint: POST http://localhost:4646/mcp
# Health check: GET  http://localhost:4646/health
```

To point an MCP client (e.g. Cursor) at the stdio server, add to its MCP
config:

```json
{
  "mcpServers": {
    "total-recall-mcp": {
      "command": "uv",
      "args": ["run", "total-recall-mcp"],
      "cwd": "/absolute/path/to/total-recall-mcp-agent"
    }
  }
}
```

### Run the tests

```bash
cd total-recall-mcp-agent

# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/test_mcp_server.py
```

### Lint & format

```bash
uv run ruff check .
uv run ruff format .
```

### Contributors
- <email 1>
- <email 2>
- <email 3>
