"""kb-agent FastAPI entrypoint — REST + MCP knowledge facade."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import AuthContext, require_bearer
from app.config import Settings, get_settings
from app.kb_service import DomainError, KbService
from kb_schema import get_session

app = FastAPI(title="kb-agent", version="0.2.0", redirect_slashes=False)


def get_db(settings: Settings = Depends(get_settings)):
    SessionLocal = get_session(settings.database_url)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_kb(
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> KbService:
    svc = KbService(session, settings)
    try:
        yield svc
    finally:
        svc.close()


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)
    user_id: str | None = None


class HitOut(BaseModel):
    knowledge_id: str
    chunk_id: str
    text: str
    score: float | None = None
    title: str | None = None
    summary: str | None = None


class SufficiencyOut(BaseModel):
    enough: bool
    reason: str | None = None


class SearchResponse(BaseModel):
    hits: list[HitOut]
    sufficiency: SufficiencyOut


class ProposeRequest(BaseModel):
    text: str = Field(min_length=1)
    title: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    auto_ingest: bool | None = None
    skip_confirm: bool | None = None
    user_id: str | None = None


class ConfirmRequest(BaseModel):
    user_id: str | None = None


class ItemPatchRequest(BaseModel):
    title: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    knowledge_type: str | None = None


class SummaryOut(BaseModel):
    knowledge_id: str
    title: str | None = None
    status: str | None = None
    summary: str | None = None
    refreshed: bool = False


def _raise_domain(exc: DomainError) -> None:
    detail: dict[str, Any] = {"code": exc.code, "message": exc.message}
    if exc.degrade_hint:
        detail["degrade_hint"] = exc.degrade_hint
    raise HTTPException(status_code=exc.status_code, detail=detail) from exc


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/kb/search", response_model=SearchResponse)
def kb_search(
    body: SearchRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> SearchResponse:
    _ = body.user_id  # agent-auth-02: ignored
    try:
        out = kb.search(user_id=auth.user_id, query=body.query, top_k=body.top_k)
    except DomainError as exc:
        _raise_domain(exc)
        raise
    return SearchResponse(
        hits=[HitOut(**h.__dict__) for h in out.hits],
        sufficiency=SufficiencyOut(enough=out.enough, reason=out.reason),
    )


@app.post("/api/v1/kb/proposals")
def create_proposal(
    body: ProposeRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    _ = body.user_id
    try:
        return kb.propose_ingest(
            user_id=auth.user_id,
            text=body.text,
            title=body.title,
            project=body.project,
            tags=body.tags,
            notes=body.notes,
            auto_ingest=body.auto_ingest,
            skip_confirm=body.skip_confirm,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.post("/api/v1/kb/proposals/{pending_id}/confirm")
def confirm_proposal(
    pending_id: str,
    body: ConfirmRequest | None = None,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    if body is not None:
        _ = body.user_id
    try:
        return kb.confirm_ingest(user_id=auth.user_id, pending_id=pending_id)
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.get("/api/v1/kb/items")
def list_items(
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
    project: str | None = None,
    tag: str | None = None,
    knowledge_type: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    items = kb.list_knowledge(
        user_id=auth.user_id,
        project=project,
        tag=tag,
        knowledge_type=knowledge_type,
        limit=limit,
    )
    return {"items": items}


@app.get("/api/v1/kb/items/{item_id}")
def get_item(
    item_id: str,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    try:
        return kb.get_item(user_id=auth.user_id, item_id=item_id)
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.patch("/api/v1/kb/items/{item_id}")
def patch_item(
    item_id: str,
    body: ItemPatchRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    try:
        return kb.update_item(
            user_id=auth.user_id,
            item_id=item_id,
            title=body.title,
            project=body.project,
            tags=body.tags,
            knowledge_type=body.knowledge_type,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.delete("/api/v1/kb/items/{item_id}")
def delete_item(
    item_id: str,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    try:
        return kb.soft_delete_item(user_id=auth.user_id, item_id=item_id)
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.get("/api/v1/kb/items/{item_id}/summary", response_model=SummaryOut)
def get_item_summary(
    item_id: str,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> SummaryOut:
    try:
        out = kb.get_knowledge_summary(
            user_id=auth.user_id,
            knowledge_id=item_id,
            refresh=False,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise
    return SummaryOut(**out)


@app.post("/api/v1/kb/items/{item_id}/summary/refresh", response_model=SummaryOut)
def refresh_item_summary(
    item_id: str,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> SummaryOut:
    try:
        out = kb.get_knowledge_summary(
            user_id=auth.user_id,
            knowledge_id=item_id,
            refresh=True,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise
    return SummaryOut(**out)


@app.get("/api/v1/kb/whoami")
def whoami(auth: AuthContext = Depends(require_bearer)) -> dict[str, str]:
    return {
        "user_id": str(auth.user_id),
        "api_key_id": str(auth.api_key_id),
        "key_prefix": auth.key_prefix,
    }


class OrganizeRequest(BaseModel):
    action: str = Field(min_length=1)
    project: str | None = None
    tag: str | None = None
    knowledge_type: str | None = None
    instruction: str | None = None
    apply: bool = False
    limit: int = Field(default=50, ge=1, le=100)
    user_id: str | None = None


class ConfirmImportRequest(BaseModel):
    pending_ids: list[str] | None = None
    confirm_all_viable: bool = False
    user_id: str | None = None


@app.post("/api/v1/kb/imports")
async def create_import(
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
    files: list[UploadFile] = File(...),
    default_project: str | None = Form(None),
    default_tags: str | None = Form(None),
) -> dict[str, Any]:
    """Multipart batch import → ImportBatch + per-file proposals (no auto-confirm)."""
    tags: list[str] | None = None
    if default_tags:
        tags = [t.strip() for t in default_tags.split(",") if t.strip()]
    payloads: list[tuple[str, bytes]] = []
    for f in files:
        name = f.filename or "untitled.txt"
        data = await f.read()
        payloads.append((name, data))
    try:
        return kb.create_import_batch(
            user_id=auth.user_id,
            files=payloads,
            default_project=default_project,
            default_tags=tags,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.get("/api/v1/kb/imports/{batch_id}")
def get_import(
    batch_id: str,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    try:
        return kb.get_import_batch(user_id=auth.user_id, batch_id=batch_id)
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.post("/api/v1/kb/imports/{batch_id}/confirm")
def confirm_import(
    batch_id: str,
    body: ConfirmImportRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    _ = body.user_id
    try:
        return kb.confirm_import_batch(
            user_id=auth.user_id,
            batch_id=batch_id,
            pending_ids=body.pending_ids,
            confirm_all_viable=body.confirm_all_viable,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.post("/api/v1/kb/organize")
def organize_kb(
    body: OrganizeRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    _ = body.user_id
    try:
        return kb.organize(
            user_id=auth.user_id,
            action=body.action,
            project=body.project,
            tag=body.tag,
            knowledge_type=body.knowledge_type,
            instruction=body.instruction,
            apply=body.apply,
            limit=body.limit,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


class FetchRequest(BaseModel):
    url: str = Field(min_length=1)
    title: str | None = None
    project: str | None = None
    tags: list[str] | None = None
    propose: bool = True


class ExternalSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    project: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


@app.post("/api/v1/kb/fetch")
def fetch_url(
    body: FetchRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    try:
        return kb.fetch_url(
            user_id=auth.user_id,
            url=body.url,
            title=body.title,
            project=body.project,
            tags=body.tags,
            propose=body.propose,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


@app.post("/api/v1/kb/sources/search")
def sources_search(
    body: ExternalSearchRequest,
    auth: AuthContext = Depends(require_bearer),
    kb: KbService = Depends(get_kb),
) -> dict[str, Any]:
    try:
        return kb.external_search(
            user_id=auth.user_id,
            query=body.query,
            project=body.project,
            top_k=body.top_k,
        )
    except DomainError as exc:
        _raise_domain(exc)
        raise


# --- optional OpenAI-compatible chat facade ---
try:
    from app.chat_facade import mount_chat_facade

    mount_chat_facade(app)
except Exception as exc:  # noqa: BLE001
    import logging

    logging.getLogger("kb-agent").exception("Chat facade mount failed: %s", exc)


# --- MCP mount (Streamable HTTP at /mcp) ---
try:
    from app.mcp_server import mount_mcp

    mount_mcp(app)
except Exception as exc:  # noqa: BLE001
    import logging

    logging.getLogger("kb-agent").exception("MCP mount failed: %s", exc)
