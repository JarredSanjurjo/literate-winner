"""Runtime settings for the application."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_DATABASE_URL = "sqlite:///data/app.db"
DEFAULT_PROMPT_VERSION = "classification_v1"
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL_NAME = "gpt-4.1-mini"


class Settings(BaseModel):
    """Application runtime settings loaded from environment variables."""

    model_config = ConfigDict(frozen=True)

    provider: str = DEFAULT_PROVIDER
    model_name: str = DEFAULT_MODEL_NAME
    database_url: str = DEFAULT_DATABASE_URL
    log_level: str = "INFO"
    prompt_version: str = DEFAULT_PROMPT_VERSION
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str | None = None

    @classmethod
    def from_env(cls, env_file: str | os.PathLike[str] | None = ".env") -> "Settings":
        """Load settings from the process environment and an optional .env file."""
        if env_file:
            load_dotenv(dotenv_path=env_file, override=False)
        else:
            load_dotenv(override=False)

        return cls(
            provider=os.getenv("AI_PROVIDER", DEFAULT_PROVIDER).lower(),
            model_name=os.getenv("OPENAI_MODEL", DEFAULT_MODEL_NAME),
            database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            prompt_version=os.getenv("PROMPT_VERSION", DEFAULT_PROMPT_VERSION),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.75")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        )

    @property
    def database_path(self) -> Path | None:
        """Return a local database path for SQLite URLs when possible."""
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        return Path(self.database_url.removeprefix(prefix))

    def validate_runtime(self) -> None:
        """Validate that the minimum runtime configuration is present."""
        if self.provider == DEFAULT_PROVIDER and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")
