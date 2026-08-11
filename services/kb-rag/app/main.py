"""kb-rag FastAPI entrypoint."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.blob_store import BlobStore, default_blob_store
from app.config import Settings, get_settings
from app.embedders import build_embedder
from app.retriever import InMemoryVectorStore, Retriever

app = FastAPI(title="kb-rag", version="0.2.0")


@lru_cache
def _build_retriever() -> Retriever:
    import os

    settings = get_settings()
    embedder = build_embedder(use_fake=settings.use_fake_embedder, dim=settings.embed_dim)
    # Process-local InMemory cannot serve agent↔rag HTTP; default to Qdrant.
    use_memory = os.environ.get("USE_INMEMORY_VECTOR_STORE", "").lower() in {"1", "true", "yes"}
    if use_memory:
        store: object = InMemoryVectorStore()
    else:
        from app.qdrant_store import QdrantVectorStore

        store = QdrantVectorStore(
            url=settings.qdrant_url,
            collection=settings.qdrant_collection,
            dim=settings.embed_dim,
        )
    return Retriever(
        store=store,  # type: ignore[arg-type]
        embedder=embedder,
        min_hits_for_enough=settings.min_hits_for_enough,
        min_top_score_for_enough=settings.min_top_score_for_enough,
    )


def get_retriever() -> Retriever:
    return _build_retriever()


def get_blob() -> BlobStore:
    return default_blob_store()


class SearchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)


class IndexRequest(BaseModel):
    user_id: str = Field(min_length=1)
    knowledge_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    status: str = "confirmed"


class HitOut(BaseModel):
    knowledge_id: str
    chunk_id: str
    text: str
    score: float | None = None


class SufficiencyOut(BaseModel):
    enough: bool
    reason: str | None = None


class SearchResponse(BaseModel):
    hits: list[HitOut]
    sufficiency: SufficiencyOut


class IndexResponse(BaseModel):
    knowledge_id: str
    chunk_ids: list[str]
    indexed: bool = True


def require_service_token(
    x_service_token: str | None = Header(default=None, alias="X-Service-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_service_token or x_service_token != settings.rag_service_token:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED"})


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/internal/search", response_model=SearchResponse, dependencies=[Depends(require_service_token)])
def internal_search(
    body: SearchRequest,
    retriever: Retriever = Depends(get_retriever),
) -> SearchResponse:
    result = retriever.search(user_id=body.user_id, query=body.query, top_k=body.top_k)
    return SearchResponse(
        hits=[
            HitOut(
                knowledge_id=h.knowledge_id,
                chunk_id=h.chunk_id,
                text=h.text,
                score=h.score,
            )
            for h in result.hits
        ],
        sufficiency=SufficiencyOut(
            enough=result.sufficiency.enough,
            reason=result.sufficiency.reason,
        ),
    )


@app.post("/internal/index", response_model=IndexResponse, dependencies=[Depends(require_service_token)])
def internal_index(
    body: IndexRequest,
    retriever: Retriever = Depends(get_retriever),
) -> IndexResponse:
    from app.indexer_guard import IndexGuardError

    try:
        chunk_ids = retriever.index_document(
            user_id=body.user_id,
            knowledge_id=body.knowledge_id,
            text=body.text,
            status=body.status,
        )
    except IndexGuardError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": getattr(exc, "code", "RAG_INDEX_NOT_CONFIRMED"), "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail={"code": "RAG_INDEX_FAILED", "message": str(exc)},
        ) from exc
    return IndexResponse(knowledge_id=body.knowledge_id, chunk_ids=chunk_ids, indexed=True)
