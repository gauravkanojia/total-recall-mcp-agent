# cockroachdb-aws-hackathon-aug-2026

Codebase for CockroachDB × AWS Hackathon – Build the Future of Agentic Memory: https://cockroachdb-ai.devpost.com

> **Holistic project overview** (architecture, all CockroachDB + AWS components, hackathon compliance): see the [repository root README](../README.md).

## Overview

`total-recall-mcp-agent` is an MCP (Model Context Protocol) agent that uses CockroachDB
as its persistent memory layer: every tool call runs inside a database transaction
and is written to `audit_logs`, while semantic memories live in a `memories` table
with a distributed vector index.

Two entry points share one bootstrap path (`app/bootstrap.py`):

- **`app/cli.py`** — stdio MCP server for Cursor / Claude Desktop (default)
- **`app/cli.py --transport streamable-http`** — Streamable HTTP (`/mcp`, `/health`) for Docker / ECS on AWS

### Hackathon tools used (≥2 required)

| Tool | How we use it |
|---|---|
| **CockroachDB Distributed Vector Indexing** | `memories` table with `VECTOR(1024)` + `CREATE VECTOR INDEX` for `remember_memory` / `recall_memory` |
| **CockroachDB Cloud Managed MCP Server** | Read-only cluster access from Cursor via `app/mcp-cloud.example.json` |
| **ccloud CLI (Agent-Ready)** | `scripts/ccloud_cluster_info.sh` — JSON cluster metadata for agents/ops |
| **CockroachDB Agent Skills (Open Source)** | Curated skills from [cockroachlabs/cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills) in `.agents/skills/` + project skill `total-recall-agentic-memory` |

### CockroachDB Agent Skills

This project uses the open-source [CockroachDB Agent Skills](https://github.com/cockroachlabs/cockroachdb-skills) ecosystem so Cursor agents have production-grade CockroachDB expertise.

**Installed skills** (`.agents/skills/`):

| Skill | Use in this project |
|---|---|
| `total-recall-agentic-memory` | Project-specific: vector memory schema, MCP tools, scripts |
| `cockroachdb-sql` | Schema design, vector DDL, query patterns |
| `setting-up-local-cluster` | Local CockroachDB dev environment |
| `reviewing-cluster-health` | CockroachDB Cloud cluster diagnostics |
| `designing-application-transactions` | Transaction patterns for audit + memory writes |
| `configuring-audit-logging` | Audit log design aligned with `audit_logs` table |

**Install or refresh skills:**

```bash
./scripts/install_cockroachdb_skills.sh          # curated subset (default)
./scripts/install_cockroachdb_skills.sh --all    # all 34 upstream skills
```

Requires Node.js 18+ (`npx`). Skills follow the [Agent Skills specification](https://agentskills.io/specification).

### AWS services used (≥1 required)

| AWS Service | Role in this agent |
|---|---|
| **Amazon Bedrock** | Titan Text Embeddings V2 (`amazon.titan-embed-text-v2:0`) generates vectors for `remember_memory` / `recall_memory` in production (`EMBEDDING_PROVIDER=bedrock`) |
| **Amazon ECS (Fargate)** | Hosts the containerized MCP agent (`total-recall-mcp-agent --transport streamable-http`) behind an ALB — see `terraform/modules/ecs/` |
| **Application Load Balancer** | Public HTTP endpoint for `/health` and `/mcp` (Streamable HTTP transport) |
| **AWS Secrets Manager** | Stores `DATABASE_URL` for the ECS task |
| **Amazon CloudWatch Logs** | ECS task logs for observability |
| **AWS IAM** | Task execution role + Bedrock `InvokeModel` permission on the task role |

**Architecture (production):** Cursor/client → ALB → ECS Fargate → Bedrock (embeddings) + CockroachDB (memory/audit/vectors)

Local dev uses `EMBEDDING_PROVIDER=fake` so you can develop without AWS credentials; production/terraform defaults to `bedrock`.

### Semantic memory

- `remember_memory(content, kind="fact", metadata=None)` — embed and persist
- `recall_memory(query, kind=None, limit=5)` — cosine search via vector index

```env
EMBEDDING_PROVIDER=fake          # local dev
EMBEDDING_PROVIDER=bedrock       # AWS production
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024
```

## Quick start (local)

```bash
cd total-recall-mcp-agent
cp app/.env.example .env
uv sync
docker compose up -d cockroach          # or: podman / existing roach-single
uv run alembic upgrade head
uv run python scripts/seed.py             # optional test user
uv run python scripts/seed_memories.py    # optional demo memories
uv run total-recall-mcp-agent                   # stdio MCP server
```

HTTP mode (Docker Compose):

```bash
docker compose up --build
# Health: http://localhost:4646/health
# MCP:    http://localhost:4646/mcp

# Or run HTTP transport directly:
uv run total-recall-mcp-agent --transport streamable-http --host 0.0.0.0 --port 4646
```

## Memory demo

```bash
chmod +x scripts/demo_memory.sh
./scripts/demo_memory.sh
```

Or run tests:

```bash
uv run pytest tests/test_memory_mcp_int.py -v
```

## Cursor MCP config

Use `app/mcp-dev.json` as a template. No authentication setup is required for the hackathon demo — memories are scoped to a default principal (`local-test-user`). In application code this is `principal_id`; the database column remains `cognito_sub` for migration compatibility. Important details:

- Logs go to **stderr** (stdout is JSON-RPC only)
- Use full path to `uv` and `uv run --frozen --directory <project-path>`
- See `app/mcp-cloud.example.json` to add CockroachDB Cloud MCP alongside this server

## CockroachDB Cloud

1. Create a cluster at https://cockroachlabs.cloud
2. Copy the SQL connection string into `.env` as `DATABASE_URL`
3. Run migrations: `uv run alembic upgrade head`
4. Inspect your cloud cluster with ccloud (cluster name required):

```bash
./scripts/ccloud_cluster_info.sh <your-cluster-name>
# or: export CCLOUD_CLUSTER_NAME=<your-cluster-name>
```

## AWS deployment (ECS Fargate)

One-command deploy (build → ECR push → Terraform apply):

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars   # fill in database_url
cd ../..
./scripts/deploy_aws.sh
```

Manual steps:

```bash
docker build -t total-recall-mcp-agent .
# tag + push to ECR ...
terraform -chdir=terraform/environments/dev apply
```

Outputs: `health_check_url`, `mcp_endpoint_url`

Terraform provisions: ECS Fargate, ALB, Secrets Manager, IAM (Bedrock invoke), default VPC.

## Submission

See [SUBMISSION.md](../SUBMISSION.md) for Devpost checklist and a 3-minute demo video script.

## Contributors

- Gaurav Kanojia

## Project structure

```bash
app/           # MCP agent (tools, services, repositories, models)
scripts/       # seed, demo, ccloud helpers
migrations/    # Alembic (users, audit_logs, memories + vector index)
terraform/     # AWS ECS dev stack
tests/         # pytest suite
```

## Tests & lint

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

