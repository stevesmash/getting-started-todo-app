"""Application configuration and shared settings."""

from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    secret_key: str = Field(
        "dev-secret-key",
        description="Secret key for signing tokens. Override in production via APP_SECRET_KEY.",
        env="APP_SECRET_KEY",
    )
    access_token_expiry_minutes: int = Field(
        60, description="Minutes until an issued access token expires."
    )
    allow_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Origins allowed by CORS middleware.",
        env="APP_ALLOW_ORIGINS",
    )

    class Config:
        env_file = ".env"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_value: str):  # type: ignore[override]
            if field_name == "allow_origins":
                return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
            return raw_value


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance to avoid repeated parsing."""

    return Settings()
