"""kb-agent FastAPI entrypoint — REST knowledge facade."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.auth import AuthContext, require_bearer
from app.config import Settings, get_settings

app = FastAPI(title="kb-agent", version="0.1.0")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)
    # Intentionally accepted then ignored — clients must not override Bearer identity.
    user_id: str | None = None


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


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/kb/search", response_model=SearchResponse)
def kb_search(
    body: SearchRequest,
    auth: AuthContext = Depends(require_bearer),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    # agent-auth-02: ignore any client-supplied user_id
    _ignored: str | None = body.user_id
    del _ignored

    payload = {
        "user_id": str(auth.user_id),
        "query": body.query,
        "top_k": body.top_k,
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{settings.rag_base_url.rstrip('/')}/internal/search",
                headers={"X-Service-Token": settings.rag_service_token},
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail={"code": "RAG_UNAVAILABLE", "message": str(exc)}) from exc

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={"code": "RAG_ERROR", "status": resp.status_code, "body": resp.text[:500]},
        )
    data: dict[str, Any] = resp.json()
    return SearchResponse(
        hits=[HitOut(**h) for h in data.get("hits", [])],
        sufficiency=SufficiencyOut(**data.get("sufficiency", {"enough": False, "reason": "no_hits"})),
    )


@app.get("/api/v1/kb/whoami")
def whoami(auth: AuthContext = Depends(require_bearer)) -> dict[str, str]:
    """Debug helper for auth tests — returns resolved identity from Bearer only."""
    return {
        "user_id": str(auth.user_id),
        "api_key_id": str(auth.api_key_id),
        "key_prefix": auth.key_prefix,
    }
