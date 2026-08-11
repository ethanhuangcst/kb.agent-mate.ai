"""Settings for kb-rag."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    rag_service_token: str = "dev-rag-token"
    blob_root: str = "/tmp/kb-blob"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "kb_chunks"
    embed_dim: int = 64
    use_fake_embedder: bool = True
    min_hits_for_enough: int = 2
    min_top_score_for_enough: float = 0.25


def get_settings() -> Settings:
    return Settings()
