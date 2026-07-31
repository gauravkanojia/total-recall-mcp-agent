FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app

# Install third-party dependencies first for layer caching (fast rebuilds
# when only source changes). --no-install-project skips installing this
# package itself, since its source isn't copied in yet at this point.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# .dockerignore keeps secrets, VCS, and local artifacts out of this copy.
COPY . .

# Now install the project itself (editable). Doing this AFTER the source is
# present is required — an editable install built before app/ exists bakes
# an empty package finder, and copying the source in afterward doesn't fix
# it (ModuleNotFoundError: No module named 'app' at runtime).
RUN uv sync --frozen --no-dev

# Run as a non-root user.
RUN useradd --create-home --uid 10001 mcp && chown -R mcp:mcp /app
USER mcp

CMD ["uv", "run", "--no-sync", "total-recall-mcp-agent", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]
