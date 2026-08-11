"""MCP mount smoke tests (auth gate + tool registration)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
)
os.environ.setdefault("API_KEY_PEPPER", "dev-api-key-pepper-change-me")

from app.main import app  # noqa: E402


def test_mcp_rejects_missing_bearer(api_client: TestClient):
    resp = api_client.post("/mcp", json={})
    assert resp.status_code == 401
    assert resp.json().get("code") == "UNAUTHORIZED"


def test_mcp_initialize_accepts_path_without_trailing_slash(api_client: TestClient):
    """Exact `/mcp` (no trailing slash) must reach Streamable HTTP (not FastAPI 404).

    Without Bearer the auth middleware returns 401 before the mount; with a forged
    Bearer the old bug still returned {"detail":"Not Found"} after auth passed.
    """
    from hashlib import sha256
    from uuid import uuid4

    from kb_schema import get_session
    from kb_schema.models import ApiKey, ApiKeyStatus, User, UserStatus

    pepper = os.environ.get("API_KEY_PEPPER", "dev-api-key-pepper-change-me")
    raw = f"kb_live_slash_{uuid4().hex}"
    Session = get_session()
    s = Session()
    user = User(display_name=f"slash-{uuid4().hex[:6]}", status=UserStatus.active)
    s.add(user)
    s.flush()
    key = ApiKey(
        user_id=user.id,
        key_hash=sha256(f"{pepper}{raw}".encode()).hexdigest(),
        key_prefix=raw[:12],
        status=ApiKeyStatus.active,
    )
    s.add(key)
    s.commit()
    uid, kid = user.id, key.id
    s.close()

    try:
        resp = api_client.post(
            "/mcp",
            headers={
                "Authorization": f"Bearer {raw}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            },
        )
        assert resp.status_code == 200, resp.text
        assert "Not Found" not in resp.text
    finally:
        s = Session()
        s.query(ApiKey).filter(ApiKey.id == kid).delete()
        s.query(User).filter(User.id == uid).delete()
        s.commit()
        s.close()


def test_sse_rejects_missing_bearer(api_client: TestClient):
    resp = api_client.get("/sse", headers={"Accept": "text/event-stream"})
    assert resp.status_code == 401
    assert resp.json().get("code") == "UNAUTHORIZED"


def test_mcp_mount_present():
    # Mounted route exists on app
    paths = []
    for r in app.routes:
        path = getattr(r, "path", None)
        if path:
            paths.append(path)
    assert any(p == "/mcp" or p.startswith("/mcp") for p in paths)
    assert any(p == "/sse" or p.startswith("/sse") for p in paths)
