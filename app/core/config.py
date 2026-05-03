"""Application settings sourced from environment variables.

All knobs that change between developer laptops, CI, and Akamai GPU VMs are
funneled through this module. ``Settings`` is the single source of truth.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration for the application."""

    model_config = SettingsConfigDict(
        env_prefix="CUDAQ_BP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    results_dir: Path = Field(
        default=REPO_ROOT / "results",
        description="Directory where run manifests and traces are written.",
    )
    log_level: str = Field(default="INFO", description="Logging level for the app.")
    default_backend: str = Field(
        default="cpu",
        description="Default backend identifier when none is specified.",
    )
    seed: int = Field(default=42, description="RNG seed for reproducibility.")

    api_host: str = Field(default="0.0.0.0", description="Bind host for the FastAPI app.")
    api_port: int = Field(default=8000, description="Port for the FastAPI app.")
    cors_origins: str = Field(
        default="",
        description="Comma-separated CORS origins. Empty disables CORS.",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.results_dir.mkdir(parents=True, exist_ok=True)
    return _settings
