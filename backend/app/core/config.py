from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Foundry Backend"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./foundry.db"
    cors_origins: str = "http://localhost:3000"
    max_resume_size_mb: int = 5
    upload_dir: Path = Path("./uploads")

    ai_provider: Literal["demo", "gemini"] = "demo"
    gemini_api_key: str | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: float = 30.0
    llm_max_retries: int = 1
    demo_mode: bool = False

    discovery_provider: str = "demo"
    company_research_provider: str = "demo"
    funding_provider: str = "demo"
    hiring_signal_provider: str = "demo"
    founder_provider: str = "demo"
    provider_timeout_seconds: float = 15.0
    provider_max_retries: int = 1

    matching_scoring_version: str = "fit_v1"
    matching_ranking_version: str = "rank_v2"
    retrieval_default_limit: int = 12

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return [origin for origin in origins if origin != "*"]

    @property
    def max_resume_size_bytes(self) -> int:
        return self.max_resume_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
