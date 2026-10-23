
import json
import os
from functools import lru_cache
from typing import Any, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Cognitive Digital Twin"
    app_env: str = "development"
    app_version: str = "0.1.0"
    database_url: str = (
        "postgresql+psycopg://postgres:change_me"
        "@localhost:5432/cognitive_twin"
    )
    database_pool_size: int = 5
    database_pool_timeout: int = 10
    database_max_overflow: int = 10

    # API & Security Configuration
    api_auth_secret: str = "dev-secret-key-change-in-production"
    api_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    api_rate_limit_per_minute: int = 60

    @field_validator("api_allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # LLM & Agentic AI Configuration
    llm_provider: str = "gemini"
    llm_model: str = "gemini-1.5-flash"
    gemini_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    agent_mode: str = "llm"  # "llm" or "deterministic"
    agent_max_steps: int = 8
    agent_max_tool_calls: int = 5

    @property
    def effective_gemini_api_key(self) -> Optional[str]:
        """Securely resolve Gemini/Google API key without logging or exposing."""
        return (
            self.gemini_api_key
            or self.google_api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
