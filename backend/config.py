"""
Configuration settings for the Multi-Agent AI Customer Support Assistant.

This module loads environment variables and provides access to configuration settings
for the application.
"""

import logging
import sys

import json
from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./techmart_dev.db"
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "./vectorstore/faiss_index"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = '.env'
        env_ignore_empty = True
        extra = 'ignore'


settings = Settings()


def validate_settings() -> bool:
    """Validate critical configuration settings at startup.

    Returns True if all critical settings are present and valid.
    Logs clear error messages for any missing or invalid settings.
    """
    is_valid = True

    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "":
        logger.error(
            "GROQ_API_KEY is not set. "
            "Add GROQ_API_KEY=your-api-key to your .env file. "
            "Get a key at https://console.groq.com/keys"
        )
        is_valid = False

    if not settings.GROQ_MODEL or settings.GROQ_MODEL.strip() == "":
        logger.warning(
            "GROQ_MODEL is not set. Defaulting to 'llama-3.1-8b-instant'. "
            "Set GROQ_MODEL in your .env to override."
        )
        settings.GROQ_MODEL = "llama-3.1-8b-instant"

    if not settings.EMBEDDING_MODEL or settings.EMBEDDING_MODEL.strip() == "":
        logger.warning(
            "EMBEDDING_MODEL is not set. Defaulting to 'sentence-transformers/all-MiniLM-L6-v2'."
        )
        settings.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    if is_valid:
        logger.info("Configuration validated successfully.")
        logger.info("  GROQ_MODEL: %s", settings.GROQ_MODEL)
        logger.info("  EMBEDDING_MODEL: %s", settings.EMBEDDING_MODEL)
        logger.info("  FAISS_INDEX_PATH: %s", settings.FAISS_INDEX_PATH)
    else:
        logger.error(
            "Configuration validation failed. The application may not work correctly."
        )

    return is_valid
