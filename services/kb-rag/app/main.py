"""kb-rag FastAPI entrypoint."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.blob_store import BlobStore, default_blob_store
from app.config import Settings, get_settings
from app.retriever import Retriever

app = FastAPI(title="kb-rag", version="0.1.0")
_retriever = Retriever()


def get_retriever() -> Retriever:
    return _retriever


def get_blob() -> BlobStore:
    return default_blob_store()


class SearchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)


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
