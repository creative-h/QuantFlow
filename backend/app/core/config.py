"""Configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the QuantFlow backend."""

    app_name: str = "QuantFlow"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "postgresql+psycopg2://quantflow:quantflow@db:5432/quantflow"
    secret_key: str = Field(min_length=32)
    zerodha_api_key: str = ""
    zerodha_api_secret: str = ""
    zerodha_redirect_url: str = ""
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings instance per process."""

    return Settings()
