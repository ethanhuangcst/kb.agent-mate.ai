#!/usr/bin/env python3
"""MVP-2 true-stack journey: real KM + real embed + Postgres + Qdrant + agent↔rag HTTP.

Usage (services already up with USE_FAKE_*=false):
  .venv/bin/python scripts/mvp2_true_stack_journey.py
"""

from __future__ import annotations

import os
import sys
import uuid
from hashlib import sha256

import httpx

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
)
PEPPER = os.environ.get("API_KEY_PEPPER", "dev-api-key-pepper-change-me")
AGENT = os.environ.get("AGENT_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
RAG = os.environ.get("RAG_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
TOKEN = os.environ.get("RAG_SERVICE_TOKEN", "dev-rag-token")


def main() -> int:
    # Fail if fake flags still on (DoD gate)
    if os.environ.get("USE_FAKE_EMBEDDER", "true").lower() in {"1", "true", "yes"}:
        print("FAIL: USE_FAKE_EMBEDDER must be false for this journey", file=sys.stderr)
        return 2
    if os.environ.get("USE_FAKE_KM", "true").lower() in {"1", "true", "yes"}:
        print("FAIL: USE_FAKE_KM must be false for this journey", file=sys.stderr)
        return 2

    from kb_schema.db import clear_engine_cache, get_session
    from kb_schema.models import ApiKey, ApiKeyStatus, KnowledgeItem, User, UserStatus

    clear_engine_cache()
    Session = get_session(DATABASE_URL)
    s = Session()
    raw = f"kb_live_true_{uuid.uuid4().hex}"
    user = User(display_name=f"true-{uuid.uuid4().hex[:6]}", status=UserStatus.active)
    s.add(user)
    s.flush()
    key = ApiKey(
        user_id=user.id,
        key_hash=sha256(f"{PEPPER}{raw}".encode()).hexdigest(),
        key_prefix=raw[:12],
        status=ApiKeyStatus.active,
    )
    s.add(key)
    s.commit()
    uid, kid = user.id, key.id
    s.close()

    headers = {"Authorization": f"Bearer {raw}"}
    marker = f"true-stack-{uuid.uuid4().hex[:10]}"
    text = (
        f"Product knowledge: {marker}. "
        "Enterprise customers get volume discounts after annual commitment review."
    )

    try:
        with httpx.Client(timeout=120.0) as c:
            assert c.get(f"{AGENT}/healthz").status_code == 200
            assert c.get(f"{RAG}/healthz").status_code == 200

            prop = c.post(
                f"{AGENT}/api/v1/kb/proposals",
                headers=headers,
                json={"text": text, "title": "True stack note", "project": "mvp2", "tags": ["true"]},
            )
            prop.raise_for_status()
            pending = prop.json()["pending_id"]
            assert prop.json()["status"] == "proposed"
            print("propose_ok", pending, "summary=", (prop.json().get("summary") or "")[:80])

            # proposed must not be in Qdrant as searchable confirmed (search may be empty)
            before = c.post(
                f"{AGENT}/api/v1/kb/search",
                headers=headers,
                json={"query": marker},
            )
            before.raise_for_status()
            assert not any(marker in h["text"] for h in before.json()["hits"]), before.json()

            conf = c.post(
                f"{AGENT}/api/v1/kb/proposals/{pending}/confirm",
                headers=headers,
                json={},
            )
            conf.raise_for_status()
            assert conf.json()["indexed"] is True
            print("confirm_ok", conf.json())

            after = c.post(
                f"{AGENT}/api/v1/kb/search",
                headers=headers,
                json={"query": marker, "top_k": 8},
            )
            after.raise_for_status()
            hits = after.json()["hits"]
            assert any(h["knowledge_id"] == pending for h in hits), hits
            assert all("knowledge_id" in h and "chunk_id" in h and "text" in h for h in hits)
            print("search_ok", "hits=", len(hits), "top_score=", hits[0].get("score"))

            listed = c.get(
                f"{AGENT}/api/v1/kb/items",
                headers=headers,
                params={"project": "mvp2", "tag": "true"},
            )
            listed.raise_for_status()
            assert any(i["knowledge_id"] == pending for i in listed.json()["items"])
            print("list_ok")

            denied = c.post(
                f"{AGENT}/api/v1/kb/proposals",
                headers=headers,
                json={"text": "x", "auto_ingest": True},
            )
            assert denied.status_code == 400
            assert denied.json()["detail"]["code"] == "OUT_OF_SCOPE_AUTO_INGEST"
            print("scope03_ok")

            # MCP initialize with Bearer
            mcp = c.post(
                f"{AGENT}/mcp",
                headers={
                    **headers,
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
                        "clientInfo": {"name": "true-stack", "version": "0"},
                    },
                },
                follow_redirects=True,
            )
            assert mcp.status_code == 200, mcp.text
            print("mcp_init_ok")

        print("TRUE_STACK_JOURNEY_PASSED")
        return 0
    finally:
        s = Session()
        s.query(KnowledgeItem).filter(KnowledgeItem.user_id == uid).delete()
        s.query(ApiKey).filter(ApiKey.id == kid).delete()
        s.query(User).filter(User.id == uid).delete()
        s.commit()
        s.close()


if __name__ == "__main__":
    raise SystemExit(main())
