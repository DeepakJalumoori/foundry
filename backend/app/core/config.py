from functools import lru_cache
from pathlib import Path

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
