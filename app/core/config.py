"""
Core application configuration using Pydantic Settings.

Loads environment variables from .env file and validates them at startup.
All settings are centralized here to avoid scattered os.environ calls.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # ── Project Metadata ──────────────────────────────────────────────
    PROJECT_NAME: str = "Document Intelligence API"
    PROJECT_DESCRIPTION: str = (
        "A scalable RESTful API for AI-powered document analysis. "
        "Upload PDFs or text files and get intelligent summaries "
        "powered by Groq (Llama 3)."
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ── Security ──────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Redis ─────────────────────────────────────────────────────────
    REDIS_URL: str

    # ── AI Provider ───────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"
    GROQ_MAX_TOKENS: int = 1024
    GROQ_TEMPERATURE: float = 0.3

    # ── Upload Limits ─────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_CONTENT_TYPES: list[str] = [
        "application/pdf",
        "text/plain",
    ]

    # ── Rate Limiting ─────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"

    # ── Pagination ────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ── CORS ──────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        weak_defaults = {
            "super_secret_key_please_change_in_production",
            "changeme",
            "secret",
        }
        if not v or v in weak_defaults:
            raise ValueError(
                "SECRET_KEY must be set to a strong random value. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
