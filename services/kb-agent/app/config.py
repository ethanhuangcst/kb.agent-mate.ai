"""kb-agent settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent"
    api_key_pepper: str = "dev-api-key-pepper-change-me"
    rag_base_url: str = "http://127.0.0.1:8001"
    rag_service_token: str = "dev-rag-token"


def get_settings() -> Settings:
    return Settings()
