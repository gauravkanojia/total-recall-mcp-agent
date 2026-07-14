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

    # AWS
    AWS_REGION: str = "us-east-1"

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
