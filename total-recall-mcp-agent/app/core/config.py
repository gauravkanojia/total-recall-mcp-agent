"""
Configuration/Settings setup class for the MCP Server
"""

from functools import lru_cache

# from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Total-Recall MCP Application configuration.

    Values are loaded from environment variables
    and optionally from a .env file.
    """

    # Application
    APP_NAME: str = "Total-Recall MCP Agent"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 4646

    # MCP transport: "stdio" for local/CLI clients (Cursor, Claude Desktop),
    # "streamable-http" (or "sse") when served over HTTP via app.cli.
    MCP_TRANSPORT: str = "stdio"

    # Database
    DATABASE_URL: str
    DATABASE_NAME: str
    # DB_HOST: str
    DB_PORT: int = 26257
    # DB_NAME: str
    # DB_USER: str
    # DB_PASSWORD: str

    # SQLAlchemy
    DATABASE_ECHO: bool = False
    # Connection pooling (pooled by default; NullPool is for tests, where
    # cached connections would cross pytest event loops)
    DATABASE_USE_NULLPOOL: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # AWS
    AWS_REGION: str = "us-east-1"

    # HTTP transport authentication
    # "github" — validate `Authorization: Bearer <token>` against the GitHub
    #            API (principal becomes "github:<login>"); MCP_STATIC_TOKENS
    #            still checked first as a fallback.
    # "static" — only MCP_STATIC_TOKENS are accepted.
    # "off"    — no auth (local development only; every caller shares the
    #            default local principal).
    HTTP_AUTH_MODE: str = "github"
    # Comma-separated "token:principal-id" pairs, e.g. "s3cret1:alice,s3cret2:bob"
    MCP_STATIC_TOKENS: str = ""
    GITHUB_API_URL: str = "https://api.github.com"
    AUTH_CACHE_TTL_SECONDS: int = 300

    # Embeddings
    EMBEDDING_PROVIDER: str = "fake"  # "fake" for local/tests, "bedrock" for AWS
    EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    EMBEDDING_DIMENSIONS: int = 1024

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached settings instance.

    Using lru_cache ensures we only load configuration once
    during application lifetime.
    """
    return Settings()


settings = get_settings()
