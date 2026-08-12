"""kb-rag tests — blob, index guard, tenant isolation."""

from __future__ import annotations

import os

# Unit TestClient path must not require a live Qdrant process.
os.environ["USE_INMEMORY_VECTOR_STORE"] = "1"

import pytest
from fastapi.testclient import TestClient

from app.blob_store import BlobStore
from app.indexer_guard import IndexGuardError, assert_indexable
from app.main import _build_retriever, app
from app.retriever import Retriever

_build_retriever.cache_clear()


def test_blob_store_roundtrip(tmp_path):
    store = BlobStore(tmp_path)
    key = store.put(b"hello knowledge")
    assert store.exists(key)
    assert store.get(key) == b"hello knowledge"
    store.delete(key)
    assert not store.exists(key)


def test_should_refuse_index_when_proposed():
    with pytest.raises(IndexGuardError):
        assert_indexable({"id": "k1", "status": "proposed", "deleted_at": None})


def test_should_allow_index_when_confirmed():
    assert_indexable({"id": "k1", "status": "confirmed", "deleted_at": None})


def test_should_isolate_hits_by_user_id():
    r = Retriever()
    r.index_chunk(user_id="u-a", knowledge_id="ka", chunk_id="c1", text="alpha secret for A")
    r.index_chunk(user_id="u-b", knowledge_id="kb", chunk_id="c2", text="beta secret for B")
    a_hits = r.search("u-a", "secret", top_k=10).hits
    b_hits = r.search("u-b", "secret", top_k=10).hits
    assert all(h.user_id == "u-a" for h in a_hits)
    assert all(h.user_id == "u-b" for h in b_hits)
    assert {h.knowledge_id for h in a_hits} == {"ka"}
    assert {h.knowledge_id for h in b_hits} == {"kb"}


def test_healthz_and_search_auth():
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    denied = client.post("/internal/search", json={"user_id": "u1", "query": "q"})
    assert denied.status_code == 401
    ok = client.post(
        "/internal/search",
        headers={"X-Service-Token": "dev-rag-token"},
        json={"user_id": "u1", "query": "nothing yet"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["hits"] == []
    assert body["sufficiency"]["enough"] is False


def test_should_index_confirmed_and_refuse_proposed_via_http():
    client = TestClient(app)
    headers = {"X-Service-Token": "dev-rag-token"}
    bad = client.post(
        "/internal/index",
        headers=headers,
        json={
            "user_id": "u1",
            "knowledge_id": "k-proposed",
            "text": "should not index",
            "status": "proposed",
        },
    )
    assert bad.status_code == 400
    ok = client.post(
        "/internal/index",
        headers=headers,
        json={
            "user_id": "u1",
            "knowledge_id": "k-ok",
            "text": "confirmed widget pricing notes for retrieval",
            "status": "confirmed",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["indexed"] is True
    search = client.post(
        "/internal/search",
        headers=headers,
        json={"user_id": "u1", "query": "widget pricing", "top_k": 5},
    )
    assert search.status_code == 200
    hits = search.json()["hits"]
    assert any(h["knowledge_id"] == "k-ok" for h in hits)
