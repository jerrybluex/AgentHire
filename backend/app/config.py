"""
Application configuration management using Pydantic Settings.
Supports environment variables and .env files.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="agenthire", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    url: Optional[str] = Field(default=None, description="Full database URL")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    echo: bool = Field(default=False, description="Echo SQL statements")
    use_sqlite: bool = Field(default=True, description="Use SQLite for development")

    @field_validator("url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info) -> str:
        """Assemble database URL from components if not provided."""
        if v:
            return v
        data = info.data
        if data.get("use_sqlite", True):
            return "sqlite+aiosqlite:///./agenthire.db"
        return (
            f"postgresql+asyncpg://{data.get('user', 'postgres')}:{data.get('password', 'postgres')}"
            f"@{data.get('host', 'localhost')}:{data.get('port', 5432)}/{data.get('name', 'agenthire')}"
        )


class RedisSettings(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database")
    password: Optional[str] = Field(default=None, description="Redis password")
    url: Optional[RedisDsn] = Field(default=None, description="Full Redis URL")

    @field_validator("url", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: Optional[str], info) -> str:
        """Assemble Redis URL from components if not provided."""
        if v:
            return v
        data = info.data
        password_part = f":{data.get('password')}@" if data.get("password") else ""
        return f"redis://{password_part}{data.get('host', 'localhost')}:{data.get('port', 6379)}/{data.get('db', 0)}"


class SecuritySettings(BaseSettings):
    """Security configuration."""

    model_config = SettingsConfigDict(env_prefix="SECURITY_")

    secret_key: Optional[str] = Field(
        default=None,
        description="Secret key for encryption (required in production)"
    )

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: Optional[str]) -> str:
        """Ensure secret key is set. Generate random one for dev if missing."""
        if v:
            return v
        import os
        env = os.environ.get("ENVIRONMENT", "development").lower()
        if env == "production":
            raise ValueError(
                "SECURITY_SECRET_KEY must be set in production. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        # Development: generate ephemeral key (changes on restart, data won't persist)
        import secrets
        return secrets.token_urlsafe(32)
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    api_key_header: str = Field(
        default="X-API-Key",
        description="Header name for API key"
    )


class CORSSettings(BaseSettings):
    """CORS configuration."""

    model_config = SettingsConfigDict(env_prefix="CORS_")

    allow_origins: List[str] = Field(
        default=["http://localhost", "http://127.0.0.1", "http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed origins"
    )
    allow_methods: List[str] = Field(
        default=["*"],
        description="Allowed HTTP methods"
    )
    allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed headers"
    )
    allow_credentials: bool = Field(
        default=True,
        description="Allow credentials"
    )
    max_age: int = Field(
        default=3600,
        description="Max age for preflight cache"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    json_format: bool = Field(
        default=False,
        description="Use JSON format for logs"
    )


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="AgentHire API", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment name")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", description="Celery result backend")

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Module-level singleton for direct imports (e.g., celery.py)
settings = get_settings()
