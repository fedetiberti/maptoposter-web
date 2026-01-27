"""
Application configuration using Pydantic Settings.
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # CORS - stored as comma-separated string, parsed to list
    cors_origins_str: str = "http://localhost:5173,http://localhost:3000"

    # Job processing
    max_workers: int = 2
    job_expiry_hours: int = 1

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Directories
    cache_dir: str = "/tmp/maptoposter-cache"
    output_dir: str = "/tmp/maptoposter-output"

    # Paths relative to backend directory
    themes_dir: str = "themes"
    fonts_dir: str = "fonts"

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]


# Create settings instance
settings = Settings()

# Update paths if running from different directory
if not os.path.exists(settings.themes_dir):
    # Try relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings.themes_dir = os.path.join(base_dir, "themes")
    settings.fonts_dir = os.path.join(base_dir, "fonts")
