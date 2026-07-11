from functools import lru_cache

from pydantic import Field
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

    # Database
    DATABASE_URL: str = Field(default="")

    # AWS
    AWS_REGION: str = "us-east-1"

    # Security: Authentication
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
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
