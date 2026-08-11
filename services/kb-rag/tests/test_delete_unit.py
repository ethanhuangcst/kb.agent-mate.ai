"""RAG delete_by_knowledge_id unit tests."""

from __future__ import annotations

from app.retriever import InMemoryVectorStore, IndexedChunk, Retriever
from app.embedders import FakeEmbedder


def test_should_delete_chunks_by_knowledge_id():
    store = InMemoryVectorStore()
    r = Retriever(store=store, embedder=FakeEmbedder(dim=8))
    r.index_document(
        user_id="u1",
        knowledge_id="k1",
        text="hello world paragraph one. " * 20,
        status="confirmed",
    )
    r.index_document(
        user_id="u1",
        knowledge_id="k2",
        text="other document text here. " * 20,
        status="confirmed",
    )
    removed = r.delete_document(user_id="u1", knowledge_id="k1")
    assert removed >= 1
    hits = r.search(user_id="u1", query="hello", top_k=10)
    assert all(h.knowledge_id != "k1" for h in hits.hits)
