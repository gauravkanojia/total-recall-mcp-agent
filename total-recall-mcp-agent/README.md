# Total Recall MCP Agent

MCP (Model Context Protocol) agent for the [CockroachDB × AWS Hackathon](https://cockroachdb-ai.devpost.com) — **Build the Future of Agentic Memory**.

> Project overview, architecture diagram, and quick start: [repository root README](../README.md).

## Overview

`total-recall-mcp-agent` uses CockroachDB as its persistent memory layer: every tool call runs inside a database transaction and is written to `audit_logs`, while semantic memories live in a `memories` table with a distributed vector index.

**Entry points** (shared bootstrap in `app/bootstrap.py`):

| Mode | Command | Use case |
|---|---|---|
| stdio (default) | `uv run total-recall-mcp-agent` | Cursor, Claude Desktop |
| Streamable HTTP | `uv run total-recall-mcp-agent --transport streamable-http` | Docker Compose, AWS ECS |

### MCP tools

| Tool | Database interaction |
|---|---|
| `health_check` | Connectivity / liveness (no writes) |
| `get_user` | Reads the caller's own row from `users` |
| `remember_memory` | Embeds content → inserts into `memories` + audit log |
| `recall_memory` | Embeds query → vector index search on `memories` + audit log |
| `list_memories` | Caller's memories newest-first (no embedding) + audit log |
| `forget_memory` | Scoped delete of one caller-owned memory + audit log |

HTTP endpoints: `/health` (liveness, static) and `/ready` (readiness — verifies the database answers `SELECT 1`, returns 503 otherwise). Both are public; `/mcp` requires auth (see [Authentication & security](#authentication--security)).

All mutating tools flow through `app/mcp/executor.py`, which guarantees audit logging on every call.

stdio is unauthenticated by design (local, single-user) — memories scope to default principal `local-test-user`.

---

## CockroachDB components

Total Recall MCP uses CockroachDB as the **persistent memory layer** — not just a backing store, but the core of agentic memory semantics.

### Hackathon tool requirements (≥2 CockroachDB tools — all four used)

| CockroachDB capability | How we use it | Where in the repo |
|---|---|---|
| **Distributed Vector Indexing** | `memories` table stores `VECTOR(1024)` embeddings; `CREATE VECTOR INDEX memories_vector_idx ON memories (principal_id, kind, embedding vector_cosine_ops)` powers `recall_memory` cosine search | `migrations/versions/b7e4f1a29c80_*.py`, `app/repositories/memory_repository.py` |
| **CockroachDB Cloud Managed MCP Server** | Read-only cluster inspection from Cursor alongside the agent (list/describe clusters, run SQL) | `app/mcp-cloud.example.json` |
| **ccloud CLI (Agent-Ready)** | JSON cluster metadata for agents and ops automation | `scripts/ccloud_cluster_info.sh` |
| **CockroachDB Agent Skills Repo (Open Source)** | Curated operational expertise for agents (SQL, transactions, health, audit) | `.agents/skills/`, `scripts/install_cockroachdb_skills.sh` |

### Schema

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Persistent user identity | `id`, `email`, `principal_id`, timestamps |
| `audit_logs` | Every MCP tool invocation | `tool_name`, `request_id`, `principal_id`, `status`, `error_message` |
| `memories` | Semantic agent memory | `principal_id`, `kind`, `content`, `metadata` (JSONB), `embedding` (VECTOR) |

Schema is managed with **Alembic** migrations under `migrations/`.

### CockroachDB-specific features in use

- **`VECTOR(1024)` type** — native vector column for embeddings (1024-dim Titan v2)
- **Vector index with `vector_cosine_ops`** — partitioned by `principal_id` for per-caller memory isolation and fast similarity search
- **`JSONB` metadata** — flexible key/value tags on memories (`kind`, custom fields)
- **Distributed SQL + transactions** — each MCP tool runs inside a DB transaction; audit + memory writes are atomic
- **`sqlalchemy-cockroachdb` + `asyncpg`** — async Python driver stack (`cockroachdb+asyncpg://...`)
- **`pgvector` SQLAlchemy integration** — `Memory.embedding.cosine_distance()` for recall queries
- **Local 3-node cluster or CockroachDB Cloud** — same schema works on the local replicated compose cluster and managed cloud clusters

### Deployment targets for CockroachDB

| Environment | Connection | Notes |
|---|---|---|
| **Local dev** | `cockroachdb+asyncpg://root@localhost:26257/total_recall_mcp_db` | 3-node replicated compose cluster (`docker-compose.yml`); survives any single node failure — see `scripts/demo_resilience.sh` |
| **CockroachDB Cloud** | TLS connection string with `sslmode=verify-full` | Set `DATABASE_URL` in `.env` or Secrets Manager |
| **Cloud MCP (read-only)** | Bearer token to `https://cockroachlabs.cloud/mcp` | Complements the agent; does not replace application memory |

### CockroachDB Agent Skills ecosystem

Skills from [cockroachlabs/cockroachdb-skills](https://github.com/cockroachlabs/cockroachdb-skills) encode CockroachDB operational expertise as machine-executable `SKILL.md` files (Agent Skills spec). They complement MCP access and the ccloud CLI by teaching agents **how** to operate CockroachDB correctly.

**This project installs:**

- **5 upstream skills** — `cockroachdb-sql`, `setting-up-local-cluster`, `reviewing-cluster-health`, `designing-application-transactions`, `configuring-audit-logging`
- **1 project skill** — `total-recall-agentic-memory` (vector memory schema, MCP tools, project scripts)

```bash
./scripts/install_cockroachdb_skills.sh          # curated subset (default)
./scripts/install_cockroachdb_skills.sh --all    # all upstream skills
```

Requires Node.js 18+. Skills live in `.agents/skills/` and are loaded automatically by Cursor.

---

## AWS services

Hackathon submissions must use **at least one AWS service**. This project uses **Amazon Bedrock** and **Amazon ECS** as primary services, with supporting AWS infrastructure for production deployment.

### Primary AWS services

| AWS service | Role | Implementation |
|---|---|---|
| **Amazon Bedrock** | Generates text embeddings via **Titan Text Embeddings V2** (`amazon.titan-embed-text-v2:0`) for `remember_memory` and `recall_memory` | `app/clients/embeddings.py` (`BedrockEmbeddingProvider`), `app/clients/aws.py` (`boto3` bedrock-runtime client) |
| **Amazon ECS (Fargate)** | Runs the containerized MCP agent (`total-recall-mcp-agent --transport streamable-http`) as a long-lived network service | `terraform/modules/ecs/`, `Dockerfile` |

### Supporting AWS services

| AWS service | Role | Implementation |
|---|---|---|
| **Application Load Balancer (ALB)** | Public HTTP entry for `/health` (liveness) and `/mcp` (Streamable HTTP transport) | `terraform/modules/ecs/main.tf` |
| **AWS Secrets Manager** | Stores `DATABASE_URL` injected into ECS tasks | `terraform/modules/secrets/` |
| **Amazon CloudWatch Logs** | ECS task log aggregation (`awslogs` driver) | `terraform/modules/ecs/main.tf` |
| **AWS IAM** | ECS task execution role (pull images, read secrets) + task role (`bedrock:InvokeModel`) | `terraform/modules/iam/` |
| **Amazon VPC** | Default VPC + public subnets for Fargate tasks | `terraform/modules/network/` |

### Environment modes

| Mode | Embedding provider | Where it runs |
|---|---|---|
| **Local development** | `EMBEDDING_PROVIDER=fake` (deterministic SHA-256 vectors, no AWS credentials) | `uv run total-recall-mcp-agent` (stdio) or Docker Compose |
| **AWS production** | `EMBEDDING_PROVIDER=bedrock` (Terraform default) | ECS Fargate behind ALB |

Production path:

```text
MCP client → ALB → ECS Fargate → Amazon Bedrock (embed) → CockroachDB (store + search)
```

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
2. Set `DATABASE_URL` in `.env` to your cloud connection string (`sslmode=verify-full`)
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
| `--skip-build` | Use `container_image` from tfvars (skip build/push) |
| `--auto-approve` | Non-interactive apply or destroy |

**Provisioned resources:** ECS cluster + service, task definition (512 CPU / 1024 MiB), ALB + target group + listener, security groups, CloudWatch log group, Secrets Manager secrets, IAM roles/policies.

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

## Authentication & security

| Transport | Auth | Principal |
|---|---|---|
| **stdio** (Cursor, Claude Desktop) | None — local single-user by design | `local-test-user` |
| **HTTP** (`/mcp` via ALB or compose) | `Authorization: Bearer <token>`, enforced by middleware | `github:<login>` or static-token mapping |

`HTTP_AUTH_MODE` controls HTTP auth:

- **`github`** (production default) — tokens are validated against the GitHub API (`GET /user`); the caller's principal becomes `github:<login>`. Use a **fine-grained PAT with zero scopes** — identity verification needs no permissions, so a leaked demo token grants nothing.
- **`static`** — only `MCP_STATIC_TOKENS` (`token:principal` pairs) are accepted; used by `docker-compose.yml` to demo two isolated memory spaces (`demo-token-alice` / `demo-token-bob`).
- **`off`** — local development only; the server logs a warning at startup.

Security properties, enforced in code:

- **Tenant isolation** — every memory read/write is scoped by `principal_id` in the repository layer; the vector index leads with `(principal_id, kind)`, so similarity search never crosses callers.
- **Durable audit trail** — every tool call writes `STARTED` → `SUCCEEDED`/`FAILED` rows to `audit_logs` in dedicated transactions, so the trail survives tool rollbacks.
- **Fail-fast TLS** — `ENVIRONMENT=production` refuses to boot without `sslmode=verify-full` in `DATABASE_URL`.
- **Sanitized errors** — validation messages pass through to MCP clients; unexpected errors return a generic message while details stay in server logs and `audit_logs`.
- **Bounded inputs** — content ≤ 8,000 chars, metadata ≤ 16 KB, recall limit ≤ 50; clean `ValueError`s instead of DB/Bedrock errors.
- **No memory content in logs** — recall results are never written to stderr/CloudWatch.
- **Container hardening** — non-root user, no dev dependencies, `.dockerignore` keeps secrets out of image layers.

Known demo limitation: the ALB listener is HTTP (no custom domain/ACM cert), so bearer tokens transit unencrypted — hence the zero-scope PAT guidance above. Production deployments should attach an ACM certificate and HTTPS listener.

---

## Project structure

```
app/           # MCP agent (tools, services, repositories, models)
scripts/       # seed, demo, deploy, ccloud, skills install helpers
migrations/    # Alembic (users, audit_logs, memories + vector index)
terraform/     # AWS deployment stack
.agents/skills/# CockroachDB Agent Skills + project skill
tests/         # pytest suite
```

### Tech stack

- **Python 3.14**, **MCP SDK** (`mcp` / FastMCP with Starlette for HTTP transport)
- **SQLAlchemy 2** (async) + **Alembic**
- **boto3** for Bedrock Runtime
- **structlog** (stderr logging — stdout reserved for MCP JSON-RPC)
- **pytest** + **ruff**

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
