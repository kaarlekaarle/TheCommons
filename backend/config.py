import os
from functools import lru_cache
from typing import Optional, Any, Dict
import json

from pydantic import ConfigDict, AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict




class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "The Commons"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_DB: str = "the_commons"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    DB_ECHO_LOG: bool = False
    TEST_DATABASE_URL: Optional[str] = None

    # Security settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CSRF_SECRET_KEY: Optional[str] = None
    CSRF_TOKEN_HEADER: str = "X-CSRF-Token"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    TEST_REDIS_URL: str = "redis://localhost:6379/1"  # Using DB 1 for tests
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS settings
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Environment
    ENV: str = os.getenv("ENV", "development")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # or "console"
    LOG_FILE: Optional[str] = None

    # Observability
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Security
    ADMIN_USERNAMES: str = os.getenv("ADMIN_USERNAMES", "")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()


def get_settings() -> Settings:
    """
    Get the application settings.
    Uses caching to avoid reloading settings on every request.
    """
    return Settings()


# Create a global settings instance
settings = get_settings()
