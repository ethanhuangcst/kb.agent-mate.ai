"""Retriever with mandatory user_id filter."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol

from app.embedders import Embedder, FakeEmbedder


@dataclass
class Hit:
    knowledge_id: str
    chunk_id: str
    text: str
    score: float | None = None
    user_id: str | None = None


@dataclass
class Sufficiency:
    enough: bool
    reason: str | None = None


@dataclass
class SearchResult:
    hits: list[Hit]
    sufficiency: Sufficiency


@dataclass
class IndexedChunk:
    chunk_id: str
    knowledge_id: str
    user_id: str
    text: str
    vector: list[float]
    status: str = "confirmed"


class VectorStore(Protocol):
    def upsert(self, chunk: IndexedChunk) -> None: ...
    def search(self, user_id: str, query_vec: list[float], top_k: int) -> list[Hit]: ...


@dataclass
class InMemoryVectorStore:
    """Simple cosine store used when Qdrant is unavailable (tests / local)."""

    chunks: list[IndexedChunk] = field(default_factory=list)

    def upsert(self, chunk: IndexedChunk) -> None:
        self.chunks = [c for c in self.chunks if c.chunk_id != chunk.chunk_id]
        self.chunks.append(chunk)

    def search(self, user_id: str, query_vec: list[float], top_k: int) -> list[Hit]:
        scored: list[Hit] = []
        for chunk in self.chunks:
            if chunk.user_id != user_id:
                continue
            if chunk.status != "confirmed":
                continue
            score = _cosine(query_vec, chunk.vector)
            scored.append(
                Hit(
                    knowledge_id=chunk.knowledge_id,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=score,
                    user_id=chunk.user_id,
                )
            )
        scored.sort(key=lambda h: h.score or 0.0, reverse=True)
        return scored[:top_k]


def _cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(a[i] * a[i] for i in range(n))) or 1.0
    nb = math.sqrt(sum(b[i] * b[i] for i in range(n))) or 1.0
    return dot / (na * nb)


class Retriever:
    """Library search — always filters by ``user_id``; empty hits are OK."""

    def __init__(
        self,
        store: VectorStore | None = None,
        embedder: Embedder | None = None,
        *,
        min_hits_for_enough: int = 2,
        min_top_score_for_enough: float = 0.25,
    ) -> None:
        self.store = store or InMemoryVectorStore()
        self.embedder = embedder or FakeEmbedder()
        self.min_hits_for_enough = min_hits_for_enough
        self.min_top_score_for_enough = min_top_score_for_enough

    def index_chunk(
        self,
        *,
        user_id: str,
        knowledge_id: str,
        chunk_id: str,
        text: str,
        status: str = "confirmed",
    ) -> None:
        from app.indexer_guard import assert_indexable

        assert_indexable({"id": knowledge_id, "status": status, "deleted_at": None})
        vector = self.embedder.embed([text])[0]
        self.store.upsert(
            IndexedChunk(
                chunk_id=chunk_id,
                knowledge_id=knowledge_id,
                user_id=user_id,
                text=text,
                vector=vector,
                status=status,
            )
        )

    def index_document(
        self,
        *,
        user_id: str,
        knowledge_id: str,
        text: str,
        status: str = "confirmed",
    ) -> list[str]:
        """Chunk + embed + upsert; returns chunk ids."""
        from uuid import uuid4

        from app.chunker import chunk_text

        chunks = chunk_text(text)
        ids: list[str] = []
        for piece in chunks:
            cid = str(uuid4())
            self.index_chunk(
                user_id=user_id,
                knowledge_id=knowledge_id,
                chunk_id=cid,
                text=piece,
                status=status,
            )
            ids.append(cid)
        return ids

    def search(self, user_id: str, query: str, top_k: int = 8) -> SearchResult:
        if not user_id:
            raise ValueError("user_id is required for search (tenant isolation)")
        if top_k < 1:
            top_k = 1
        query_vec = self.embedder.embed([query])[0]
        hits = self.store.search(user_id=user_id, query_vec=query_vec, top_k=top_k)
        hits = [h for h in hits if h.user_id is None or h.user_id == user_id]
        sufficiency = self._sufficiency(hits)
        return SearchResult(hits=hits, sufficiency=sufficiency)

    def _sufficiency(self, hits: list[Hit]) -> Sufficiency:
        if not hits:
            return Sufficiency(enough=False, reason="no_hits")
        top = hits[0].score if hits[0].score is not None else 0.0
        if len(hits) < self.min_hits_for_enough:
            return Sufficiency(enough=False, reason="too_few_hits")
        if top < self.min_top_score_for_enough:
            return Sufficiency(enough=False, reason="low_top_score")
        return Sufficiency(enough=True, reason=None)
