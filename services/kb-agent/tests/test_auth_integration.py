"""Agent auth + search integration against real Postgres + mocked RAG HTTP."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
)
os.environ.setdefault("API_KEY_PEPPER", "dev-api-key-pepper-change-me")
os.environ.setdefault("RAG_SERVICE_TOKEN", "dev-rag-token")

from kb_schema.db import clear_engine_cache, get_engine, get_session  # noqa: E402
from kb_schema.models import ApiKey, ApiKeyStatus, User, UserStatus  # noqa: E402
from app.auth import hash_api_key  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

PEPPER = os.environ["API_KEY_PEPPER"]


def _db_available() -> bool:
    try:
        clear_engine_cache()
        engine = get_engine(os.environ["DATABASE_URL"])
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not available on :5434")


@pytest.fixture()
def issued_key():
    """Create a user + active API key; yield (raw_key, user_id); cleanup after."""
    clear_engine_cache()
    SessionLocal = get_session(os.environ["DATABASE_URL"])
    session = SessionLocal()
    raw = f"kb_live_test_{uuid.uuid4().hex}"
    user = User(display_name=f"IT-{uuid.uuid4().hex[:8]}", status=UserStatus.active)
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
    session.query(ApiKey).filter(ApiKey.id == key_id).delete()
    session.query(User).filter(User.id == user_id).delete()
    session.commit()
    session.close()


# client fixture: tests/conftest.py (module-scoped)
@pytest.fixture()
def client(api_client: TestClient) -> TestClient:
    clear_engine_cache()
    return api_client


def test_bearer_whoami_resolves_user(client: TestClient, issued_key):
    raw, user_id, _key_id = issued_key
    resp = client.get("/api/v1/kb/whoami", headers={"Authorization": f"Bearer {raw}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == str(user_id)


def test_body_user_id_ignored(client: TestClient, issued_key, monkeypatch: pytest.MonkeyPatch):
    raw, user_id, _ = issued_key
    seen: list[uuid.UUID] = []

    def fake_search(self, *, user_id, query, top_k=8):  # noqa: ANN001
        seen.append(user_id)
        from app.kb_service import SearchOutcome

        return SearchOutcome(hits=[], enough=False, reason="no_hits")

    monkeypatch.setattr("app.kb_service.KbService.search", fake_search)
    resp = client.post(
        "/api/v1/kb/search",
        headers={"Authorization": f"Bearer {raw}"},
        json={"query": "hello", "user_id": "attacker-other-user"},
    )
    assert resp.status_code == 200
    assert seen == [user_id]


def test_revoked_key_is_401(client: TestClient, issued_key):
    raw, _user_id, key_id = issued_key
    SessionLocal = get_session(os.environ["DATABASE_URL"])
    session = SessionLocal()
    row = session.get(ApiKey, key_id)
    assert row is not None
    row.status = ApiKeyStatus.revoked
    row.revoked_at = datetime.now(timezone.utc)
    session.commit()
    session.close()

    resp = client.get("/api/v1/kb/whoami", headers={"Authorization": f"Bearer {raw}"})
    assert resp.status_code == 401


def test_same_key_multiple_clients(client: TestClient, issued_key):
    raw, user_id, _ = issued_key
    a = client.get("/api/v1/kb/whoami", headers={"Authorization": f"Bearer {raw}"})
    b = client.get("/api/v1/kb/whoami", headers={"Authorization": f"Bearer {raw}"})
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()["user_id"] == b.json()["user_id"] == str(user_id)


def test_empty_search_sufficiency_false(client: TestClient, issued_key, monkeypatch: pytest.MonkeyPatch):
    raw, user_id, _ = issued_key
    seen: list[uuid.UUID] = []

    def fake_search(self, *, user_id, query, top_k=8):  # noqa: ANN001
        seen.append(user_id)
        from app.kb_service import SearchOutcome

        return SearchOutcome(hits=[], enough=False, reason="no_hits")

    monkeypatch.setattr("app.kb_service.KbService.search", fake_search)
    resp = client.post(
        "/api/v1/kb/search",
        headers={"Authorization": f"Bearer {raw}"},
        json={"query": "anything"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["hits"] == []
    assert body["sufficiency"]["enough"] is False
    assert seen == [user_id]


def test_settings_default_pepper():
    s = get_settings()
    assert s.api_key_pepper
