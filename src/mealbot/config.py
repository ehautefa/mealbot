"""Configuration management for MealBot."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str = ""

    # Anthropic
    anthropic_api_key: str = ""

    # Coop.ch
    coop_username: str = ""
    coop_password: str = ""

    # Database
    database_path: str = "./mealbot.db"

    # Timezone
    timezone: str = "Europe/Zurich"

    # Claude model
    claude_model: str = "claude-sonnet-4-20250514"


# Global settings instance
settings = Settings()
