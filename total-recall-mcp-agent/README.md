# cockroachdb-aws-hackathon-aug-2026
Codebase for CockroachDB × AWS Hackathon – Build the Future of Agentic Memory (the “Hackathon”): https://cockroachdb-ai.devpost.com

## Overview

`total-recall-mcp` is ....


### Project Structure

```bash
.
├── app
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   └── v1
│   │       ├── __init__.py
│   │       ├── endpoints
│   │       │   ├── __init__.py
│   │       │   ├── health.py
│   │       │   └── users.py
│   │       └── router.py
│   ├── auth
│   │   ├── __init__.py
│   │   ├── cognito.py
│   │   ├── dependencies.py
│   │   └── jwt.py
│   ├── cli.py
│   ├── clients
│   │   ├── __init__.py
│   │   ├── aws.py
│   │   └── cockroach_db.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── audit.py
│   │   │   ├── base.py
│   │   │   └── user.py
│   │   └── session.py
│   ├── dependencies
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   └── services.py
│   ├── exceptions
│   │   ├── __init__.py
│   │   └── handlers.py
│   ├── main.py
│   ├── mcp
│   │   ├── __init__.py
│   │   ├── context.py
│   │   ├── middleware.py
│   │   ├── registry.py
│   │   └── server.py
│   ├── middleware
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── request_id.py
│   ├── repositories
│   │   ├── __init__.py
│   │   └── user_repository.py
│   ├── schemas
│   │   ├── __init__.py
│   │   └── user.py
│   ├── services
│   │   ├── __init__.py
│   │   └── user_service.py
│   └── tools
│       ├── __init__.py
│       ├── health.py
│       ├── sql.py
│       └── users.py
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── pyproject.toml
├── README.md
├── scripts
│   ├── __init__.py
│   ├── python_commands.sh
│   └── seed.py
├── terraform
│   ├── environments
│   │   ├── dev
│   │   │   ├── main.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── variables.tf
│   │   └── stage
│   │       ├── main.tf
│   │       ├── terraform.tfvars
│   │       └── variables.tf
│   ├── main.tf
│   └── modules
│       ├── ecs
│       │   └── main.tf
│       ├── iam
│       │   └── main.tf
│       ├── network
│       │   └── main.tf
│       └── secrets
│           └── main.tf
├── tests
│   ├── test_config.py
│   ├── test_health.py
│   ├── test_logging.py
│   ├── test_mcp_server.py
│   └── test_users.py
└── uv.lock
```

### How to run the MCP CLI

```bash
# Change the directory to MCP server project
cd total-recall-mcp-agent

# Sync the project
uv sync

# Run the MCP Server CLI
uv run python -m app.cli
```

### Run the tests

```bash
# Change the directory to MCP server project
cd total-recall-mcp-agent

# Run all tests
uv run pytest tests/*

# Run specific tests
uv run pytest tests/test_mcp_server.py
```

### Contributors
- <email 1>
- <email 2>
- <email 3>
