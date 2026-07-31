# Total Recall MCP Agent

MCP (Model Context Protocol) agent for the [CockroachDB × AWS Hackathon](https://cockroachdb-ai.devpost.com) — **Build the Future of Agentic Memory**.

> Architecture, hackathon compliance, and component map: [repository root README](../README.md).

## Overview

`total-recall-mcp-agent` uses CockroachDB as its persistent memory layer: every tool call runs inside a database transaction and is written to `audit_logs`, while semantic memories live in a `memories` table with a distributed vector index.

**Entry points** (shared bootstrap in `app/bootstrap.py`):

| Mode | Command | Use case |
|---|---|---|
| stdio (default) | `uv run total-recall-mcp-agent` | Cursor, Claude Desktop |
| Streamable HTTP | `uv run total-recall-mcp-agent --transport streamable-http` | Docker Compose, AWS ECS |

### MCP tools

| Tool | Description |
|---|---|
| `health_check` | Service liveness |
| `get_user` | Return the caller's own user record (scoped by principal) |
| `remember_memory` | Embed and persist semantic memory |
| `recall_memory` | Vector similarity search over memories |

No authentication is required for evaluation — memories are scoped to default principal `local-test-user` (`principal_id` in code; `principal_id` column in DB).

---

## Hackathon tools & AWS services

### CockroachDB (≥2 required — all four used)

| Tool | How we use it |
|---|---|
| **Distributed Vector Indexing** | `memories` table with `VECTOR(1024)` + vector index for `remember_memory` / `recall_memory` |
| **Cloud Managed MCP Server** | Read-only cluster access via `app/mcp-cloud.example.json` |
| **ccloud CLI (Agent-Ready)** | `scripts/ccloud_cluster_info.sh <cluster-name>` — JSON cluster metadata |
| **Agent Skills (Open Source)** | `.agents/skills/` + `scripts/install_cockroachdb_skills.sh` |

### AWS (≥1 required)

| Service | Role |
|---|---|
| **Amazon Bedrock** | Titan Text Embeddings V2 for production embeddings |
| **Amazon ECS Fargate** | Containerized MCP agent behind ALB |
| **ALB** | Public `/health` and `/mcp` endpoints |
| **Secrets Manager** | `DATABASE_URL` for ECS tasks |
| **CloudWatch Logs** | ECS task logs |
| **IAM** | Task roles including `bedrock:InvokeModel` |

Local dev uses `EMBEDDING_PROVIDER=fake` (no AWS credentials). Production/terraform defaults to `bedrock`.

---

## Prerequisites

| Tool | Local | AWS deploy |
|---|---|---|
| Python 3.14+ | Yes | (in Docker image) |
| [uv](https://docs.astral.sh/uv/) | Yes | Yes |
| Docker / Podman | Yes | Yes (build/push) |
| CockroachDB | Local Docker or Cloud | CockroachDB Cloud recommended |
| AWS CLI + Terraform >= 1.5 | No | Yes |
| Bedrock model access | No | Yes (Titan Embeddings v2) |

---

## Local setup

```bash
cd total-recall-mcp-agent
cp app/.env.example .env
uv sync
docker compose up -d
uv run alembic upgrade head
uv run python scripts/seed.py           # optional test user
uv run python scripts/seed_memories.py  # optional demo memories
```

Default `.env` values work with Docker Compose Cockroach:

```env
DATABASE_URL=cockroachdb+asyncpg://root@localhost:26257/total_recall_mcp_db
DATABASE_NAME=total_recall_mcp_db
EMBEDDING_PROVIDER=fake
```

---

## Run locally

### stdio MCP (Cursor)

```bash
uv run total-recall-mcp-agent
```

Configure Cursor using `app/mcp-dev.json`:

- Set `--directory` to your **absolute** project path
- Keep `EMBEDDING_PROVIDER=fake` in `env`
- Logs go to **stderr** (stdout is JSON-RPC only)

Or use the launcher:

```bash
chmod +x scripts/run_mcp_stdio.sh
./scripts/run_mcp_stdio.sh
```

### Streamable HTTP

```bash
uv run total-recall-mcp-agent --transport streamable-http --host 0.0.0.0 --port 4646
```

Or via Docker Compose:

```bash
docker compose up --build
```

Endpoints: http://localhost:4646/health · http://localhost:4646/mcp

### Memory demo

```bash
chmod +x scripts/demo_memory.sh
./scripts/demo_memory.sh
```

---

## Validate locally

**Health:**

```bash
curl -s http://localhost:4646/health
```

**Tests:**

```bash
# Default: unit tests always run; integration auto-skips if DB is down
uv run pytest

# Unit tests only
uv run pytest -m "not integration"

# Integration only (when CockroachDB is running + migrated)
uv run alembic upgrade head
uv run pytest -m integration
uv run pytest tests/test_memory_mcp_int.py -v
```

**CockroachDB persistence** (after using MCP tools):

```sql
SELECT tool_name, status, principal_id AS principal_id
FROM audit_logs ORDER BY created_at DESC LIMIT 5;

SELECT kind, content, principal_id AS principal_id
FROM memories ORDER BY created_at DESC LIMIT 5;
```

---

## CockroachDB Cloud (optional)

1. Create a cluster at https://cockroachlabs.cloud
2. Set `DATABASE_URL` in `.env` to your cloud connection string
3. Run `uv run alembic upgrade head`
4. Inspect cluster metadata:

```bash
./scripts/ccloud_cluster_info.sh <your-cluster-name>
```

Add read-only Cloud MCP in Cursor via `app/mcp-cloud.example.json`.

---

## AWS deployment

Terraform provisions ECS Fargate, ALB, Secrets Manager, IAM, and CloudWatch. **CockroachDB is external** — use CockroachDB Cloud and pass `database_url` in tfvars.

### 1. Prepare AWS

```bash
aws configure
aws sts get-caller-identity
```

Enable **Amazon Titan Text Embeddings V2** in Bedrock (same region as deploy, default `us-east-1`).

### 2. Configure Terraform

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` — set `database_url` to your CockroachDB Cloud asyncpg URL:

```
cockroachdb+asyncpg://<user>:<password>@<host>:26257/total_recall_mcp_db?sslmode=verify-full
```

Run migrations against that database from your laptop before deploying.

```bash
terraform init
```

### 3. Deploy

From project root:

```bash
chmod +x scripts/deploy_aws.sh
./scripts/deploy_aws.sh plan        # preview changes
./scripts/deploy_aws.sh apply       # build, push ECR, deploy
./scripts/deploy_aws.sh destroy     # tear down when finished
```

| Flag | Effect |
|---|---|
| `--skip-build` | Use `container_image` from tfvars (skip Docker/ECR) |
| `--auto-approve` | Non-interactive apply or destroy |

### 4. Validate AWS endpoints

```bash
cd terraform/environments/dev
terraform output

curl -s "$(terraform output -raw health_check_url)"
```

Expected health response: `{"status":"ok","service":"Total-Recall MCP Agent"}`

MCP endpoint: `terraform output -raw mcp_endpoint_url` (streamable HTTP on `/mcp`).

**ECS logs** if tasks fail:

```bash
aws logs tail /ecs/total-recall-mcp-agent-dev --follow --region us-east-1
```

---

## CockroachDB Agent Skills

```bash
./scripts/install_cockroachdb_skills.sh          # curated subset (default)
./scripts/install_cockroachdb_skills.sh --all    # all upstream skills
```

Requires Node.js 18+. Skills live in `.agents/skills/`.

---

## Project structure

```
app/           # MCP agent (tools, services, repositories, models)
scripts/       # seed, demo, deploy, ccloud helpers
migrations/    # Alembic (users, audit_logs, memories + vector index)
terraform/     # AWS deployment stack
tests/         # pytest suite
```

## Tests & lint

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## License

MIT — see [LICENSE](../LICENSE)

## Contributors

- Gaurav Kanojia
