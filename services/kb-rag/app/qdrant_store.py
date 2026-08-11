"""Qdrant-backed vector store with mandatory user_id filter."""

from __future__ import annotations

from typing import Any

from app.retriever import Hit, IndexedChunk


class QdrantVectorStore:
    def __init__(
        self,
        *,
        url: str,
        collection: str,
        dim: int,
    ) -> None:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qm

        self._qm = qm
        self.dim = dim
        self.collection = collection
        self.client = QdrantClient(url=url, check_compatibility=False)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        names = {c.name for c in self.client.get_collections().collections}
        if self.collection in names:
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=self._qm.VectorParams(size=self.dim, distance=self._qm.Distance.COSINE),
        )
        self.client.create_payload_index(
            collection_name=self.collection,
            field_name="user_id",
            field_schema=self._qm.PayloadSchemaType.KEYWORD,
        )

    def upsert(self, chunk: IndexedChunk) -> None:
        self.client.upsert(
            collection_name=self.collection,
            points=[
                self._qm.PointStruct(
                    id=chunk.chunk_id,
                    vector=chunk.vector,
                    payload={
                        "user_id": chunk.user_id,
                        "knowledge_id": chunk.knowledge_id,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "status": chunk.status,
                    },
                )
            ],
        )

    def search(self, user_id: str, query_vec: list[float], top_k: int) -> list[Hit]:
        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vec,
            limit=top_k,
            query_filter=self._qm.Filter(
                must=[
                    self._qm.FieldCondition(
                        key="user_id",
                        match=self._qm.MatchValue(value=user_id),
                    ),
                    self._qm.FieldCondition(
                        key="status",
                        match=self._qm.MatchValue(value="confirmed"),
                    ),
                ]
            ),
            with_payload=True,
        )
        hits: list[Hit] = []
        for p in response.points:
            payload: dict[str, Any] = p.payload or {}
            hits.append(
                Hit(
                    knowledge_id=str(payload.get("knowledge_id", "")),
                    chunk_id=str(payload.get("chunk_id", p.id)),
                    text=str(payload.get("text", "")),
                    score=float(p.score) if p.score is not None else None,
                    user_id=str(payload.get("user_id", user_id)),
                )
            )
        return hits

    def delete_by_knowledge_id(self, user_id: str, knowledge_id: str) -> int:
        result = self.client.delete(
            collection_name=self.collection,
            points_selector=self._qm.FilterSelector(
                filter=self._qm.Filter(
                    must=[
                        self._qm.FieldCondition(
                            key="user_id",
                            match=self._qm.MatchValue(value=user_id),
                        ),
                        self._qm.FieldCondition(
                            key="knowledge_id",
                            match=self._qm.MatchValue(value=knowledge_id),
                        ),
                    ]
                )
            ),
        )
        # Qdrant may not return a count; treat as success
        _ = result
        return 0
