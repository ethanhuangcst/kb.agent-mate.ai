"""kb-agent settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    database_url: str = "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent"
    api_key_pepper: str = "dev-api-key-pepper-change-me"
    rag_base_url: str = "http://127.0.0.1:8001"
    rag_service_token: str = "dev-rag-token"
    blob_root: str = "./data/blob"
    use_fake_km: bool = True
    qwen_api_key: str | None = None
    qwen_base_url: str | None = None
    qwen_chat_model: str | None = None


def get_settings() -> Settings:
    return Settings()
