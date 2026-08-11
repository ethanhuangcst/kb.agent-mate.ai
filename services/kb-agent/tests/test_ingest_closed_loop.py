"""Propose → confirm → search → list against Postgres + live RAG HTTP."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
)
os.environ.setdefault("API_KEY_PEPPER", "dev-api-key-pepper-change-me")
os.environ.setdefault("RAG_SERVICE_TOKEN", "dev-rag-token")
os.environ.setdefault("RAG_BASE_URL", "http://127.0.0.1:8001")
os.environ.setdefault("USE_FAKE_KM", "true")

from kb_schema.db import clear_engine_cache, get_engine, get_session  # noqa: E402
from kb_schema.models import ApiKey, ApiKeyStatus, KnowledgeItem, User, UserStatus  # noqa: E402
from app.auth import hash_api_key  # noqa: E402
from app.main import app  # noqa: E402

PEPPER = os.environ["API_KEY_PEPPER"]
RAG_URL = os.environ["RAG_BASE_URL"].rstrip("/")
TOKEN = os.environ["RAG_SERVICE_TOKEN"]


def _db_ok() -> bool:
    try:
        clear_engine_cache()
        with get_engine(os.environ["DATABASE_URL"]).connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


def _rag_ok() -> bool:
    try:
        r = httpx.get(f"{RAG_URL}/healthz", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_db_ok() and _rag_ok()),
    reason="Postgres :5434 or RAG :8001 unavailable",
)


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, api_client: TestClient) -> TestClient:
    clear_engine_cache()
    monkeypatch.setenv("BLOB_ROOT", str(tmp_path / "blob"))
    monkeypatch.setenv("USE_FAKE_KM", "true")
    from app import config as cfg

    monkeypatch.setattr(
        cfg,
        "get_settings",
        lambda: cfg.Settings(
            database_url=os.environ["DATABASE_URL"],
            api_key_pepper=PEPPER,
            rag_base_url=RAG_URL,
            rag_service_token=TOKEN,
            blob_root=str(tmp_path / "blob"),
            use_fake_km=True,
        ),
    )
    return api_client


@pytest.fixture()
def issued_key():
    clear_engine_cache()
    SessionLocal = get_session(os.environ["DATABASE_URL"])
    session = SessionLocal()
    raw = f"kb_live_test_{uuid.uuid4().hex}"
    user = User(display_name=f"CL-{uuid.uuid4().hex[:8]}", status=UserStatus.active)
    session.add(user)
    session.flush()
    key = ApiKey(
        user_id=user.id,
        key_hash=hash_api_key(raw, PEPPER),
        key_prefix=raw[:12],
        status=ApiKeyStatus.active,
    )
    session.add(key)
    session.commit()
    user_id = user.id
    key_id = key.id
    session.close()
    yield raw, user_id, key_id
    session = SessionLocal()
    session.query(KnowledgeItem).filter(KnowledgeItem.user_id == user_id).delete()
    session.query(ApiKey).filter(ApiKey.id == key_id).delete()
    session.query(User).filter(User.id == user_id).delete()
    session.commit()
    session.close()


def test_propose_confirm_search_list_closed_loop(client: TestClient, issued_key):
    raw, user_id, _ = issued_key
    headers = {"Authorization": f"Bearer {raw}"}
    marker = f"acme-widget-pricing-{uuid.uuid4().hex}"
    text = f"Internal note: {marker} discount rules for enterprise accounts."

    # proposed must not appear in search yet — index only after confirm
    prop = client.post(
        "/api/v1/kb/proposals",
        headers=headers,
        json={"text": text, "title": "Acme pricing", "project": "mvp2", "tags": ["pricing"]},
    )
    assert prop.status_code == 200, prop.text
    body = prop.json()
    pending_id = body["pending_id"]
    assert body["status"] == "proposed"

    search_before = client.post(
        "/api/v1/kb/search",
        headers=headers,
        json={"query": marker},
    )
    assert search_before.status_code == 200
    assert not any(marker in h["text"] for h in search_before.json()["hits"])

    conf = client.post(
        f"/api/v1/kb/proposals/{pending_id}/confirm",
        headers=headers,
        json={},
    )
    assert conf.status_code == 200, conf.text
    assert conf.json()["status"] == "confirmed"
    assert conf.json()["indexed"] is True

    search_after = client.post(
        "/api/v1/kb/search",
        headers=headers,
        json={"query": marker, "top_k": 8},
    )
    assert search_after.status_code == 200
    hits = search_after.json()["hits"]
    assert any(h["knowledge_id"] == pending_id for h in hits), hits

    listed = client.get(
        "/api/v1/kb/items",
        headers=headers,
        params={"project": "mvp2", "tag": "pricing"},
    )
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert any(i["knowledge_id"] == pending_id for i in items)


def test_should_reject_auto_ingest_via_rest(client: TestClient, issued_key):
    raw, _, _ = issued_key
    resp = client.post(
        "/api/v1/kb/proposals",
        headers={"Authorization": f"Bearer {raw}"},
        json={"text": "x", "auto_ingest": True},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "OUT_OF_SCOPE_AUTO_INGEST"
