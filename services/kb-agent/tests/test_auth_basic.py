"""Agent auth unit tests (DB-free hash + override semantics via TestClient mocks later)."""

from __future__ import annotations

from app.auth import hash_api_key
from app.main import app
from fastapi.testclient import TestClient


def test_hash_api_key_is_stable():
    a = hash_api_key("kb_live_abc", "pepper")
    b = hash_api_key("kb_live_abc", "pepper")
    c = hash_api_key("kb_live_abc", "other")
    assert a == b
    assert a != c
    assert len(a) == 64


def test_healthz():
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"


def test_search_without_bearer_is_401():
    client = TestClient(app)
    resp = client.post("/api/v1/kb/search", json={"query": "hello"})
    assert resp.status_code == 401
