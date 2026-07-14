FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "total-recall-mcp-agent", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]
