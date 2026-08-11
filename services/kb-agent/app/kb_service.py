"""Domain service shared by REST and MCP facades."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.km_client import KmClient, build_km_client, truncate_summary
from kb_schema.models import KnowledgeItem, KnowledgeStatus


class DomainError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass
class SearchHit:
    knowledge_id: str
    chunk_id: str
    text: str
    score: float | None = None
    title: str | None = None
    summary: str | None = None


@dataclass
class SearchOutcome:
    hits: list[SearchHit]
    enough: bool
    reason: str | None


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


class KbService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        *,
        km: KmClient | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.km = km or build_km_client(settings)
        self._http = http_client
        self._owns_http = http_client is None

    def close(self) -> None:
        if self._owns_http and self._http is not None:
            self._http.close()

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=60.0)
        return self._http

    def search(self, *, user_id: UUID, query: str, top_k: int = 8) -> SearchOutcome:
        payload = {"user_id": str(user_id), "query": query, "top_k": top_k}
        try:
            resp = self._client().post(
                f"{self.settings.rag_base_url.rstrip('/')}/internal/search",
                headers={"X-Service-Token": self.settings.rag_service_token},
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise DomainError("RAG_UNAVAILABLE", str(exc), status_code=502) from exc
        if resp.status_code != 200:
            raise DomainError("RAG_ERROR", resp.text[:500], status_code=502)
        data = resp.json()
        hits = [
            SearchHit(
                knowledge_id=h["knowledge_id"],
                chunk_id=h["chunk_id"],
                text=h["text"],
                score=h.get("score"),
            )
            for h in data.get("hits", [])
        ]
        self._enrich_hits_with_summary(user_id=user_id, hits=hits)
        suf = data.get("sufficiency") or {}
        return SearchOutcome(
            hits=hits,
            enough=bool(suf.get("enough", False)),
            reason=suf.get("reason"),
        )

    def _enrich_hits_with_summary(self, *, user_id: UUID, hits: list[SearchHit]) -> None:
        ids: list[UUID] = []
        for h in hits:
            try:
                ids.append(UUID(h.knowledge_id))
            except ValueError:
                continue
        if not ids:
            return
        rows = list(
            self.session.scalars(
                select(KnowledgeItem).where(
                    KnowledgeItem.user_id == user_id,
                    KnowledgeItem.id.in_(ids),
                    KnowledgeItem.deleted_at.is_(None),
                )
            )
        )
        by_id = {str(r.id): r for r in rows}
        for h in hits:
            row = by_id.get(h.knowledge_id)
            if row is None:
                continue
            h.title = row.title
            h.summary = truncate_summary(row.summary) if row.summary else None

    def propose_ingest(
        self,
        *,
        user_id: UUID,
        text: str,
        title: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        auto_ingest: bool | None = None,
        skip_confirm: bool | None = None,
    ) -> dict[str, Any]:
        if auto_ingest or skip_confirm:
            raise DomainError(
                "OUT_OF_SCOPE_AUTO_INGEST",
                "Auto-ingest / skip confirm is not allowed; use propose then confirm.",
            )
        body = (text or "").strip()
        if not body:
            raise DomainError("INVALID_TEXT", "text is required")

        digest = content_hash(body)
        existing = self.session.scalar(
            select(KnowledgeItem).where(
                KnowledgeItem.user_id == user_id,
                KnowledgeItem.content_hash == digest,
                KnowledgeItem.deleted_at.is_(None),
            )
        )
        if existing is not None:
            return {
                "pending_id": str(existing.id),
                "status": existing.status.value,
                "summary": existing.summary,
                "suggested_type": existing.knowledge_type,
                "duplicate_hint": True,
                "title": existing.title,
            }

        meta = self.km.propose_metadata(text=body, title=title)
        overview = truncate_summary(meta.get("summary"))
        blob_key = digest
        root = self.settings.blob_root
        from pathlib import Path

        path = Path(root) / blob_key[:2] / blob_key[2:4] / blob_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body.encode("utf-8"))

        item = KnowledgeItem(
            id=uuid4(),
            user_id=user_id,
            content_hash=digest,
            title=meta.get("title") or title or body[:80],
            summary=overview,
            body_uri=blob_key,
            knowledge_type=meta.get("knowledge_type"),
            status=KnowledgeStatus.proposed,
            project=project,
            tags=list(tags or meta.get("tags") or []),
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return {
            "pending_id": str(item.id),
            "status": item.status.value,
            "summary": item.summary,
            "suggested_type": item.knowledge_type,
            "duplicate_hint": False,
            "title": item.title,
        }

    def confirm_ingest(self, *, user_id: UUID, pending_id: str) -> dict[str, Any]:
        try:
            kid = UUID(pending_id)
        except ValueError as exc:
            raise DomainError("PENDING_NOT_FOUND", "invalid pending_id") from exc

        item = self.session.get(KnowledgeItem, kid)
        if item is None or item.user_id != user_id or item.deleted_at is not None:
            raise DomainError("PENDING_NOT_FOUND", "pending not found", status_code=404)

        if item.status == KnowledgeStatus.confirmed:
            return {"knowledge_id": str(item.id), "status": "confirmed", "indexed": True}

        if item.status != KnowledgeStatus.proposed:
            raise DomainError("PENDING_NOT_FOUND", f"cannot confirm status={item.status.value}")

        text = self._load_body(item)
        item.status = KnowledgeStatus.confirmed
        item.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        try:
            resp = self._client().post(
                f"{self.settings.rag_base_url.rstrip('/')}/internal/index",
                headers={"X-Service-Token": self.settings.rag_service_token},
                json={
                    "user_id": str(user_id),
                    "knowledge_id": str(item.id),
                    "text": text,
                    "status": "confirmed",
                },
            )
        except httpx.HTTPError as exc:
            item.status = KnowledgeStatus.proposed
            self.session.commit()
            raise DomainError("RAG_UNAVAILABLE", str(exc), status_code=502) from exc

        if resp.status_code != 200:
            item.status = KnowledgeStatus.proposed
            self.session.commit()
            raise DomainError("RAG_INDEX_FAILED", resp.text[:500], status_code=502)

        return {"knowledge_id": str(item.id), "status": "confirmed", "indexed": True}

    def list_knowledge(
        self,
        *,
        user_id: UUID,
        project: str | None = None,
        tag: str | None = None,
        knowledge_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        q = select(KnowledgeItem).where(
            KnowledgeItem.user_id == user_id,
            KnowledgeItem.status == KnowledgeStatus.confirmed,
            KnowledgeItem.deleted_at.is_(None),
        )
        if project:
            q = q.where(KnowledgeItem.project == project)
        if knowledge_type:
            q = q.where(KnowledgeItem.knowledge_type == knowledge_type)
        q = q.order_by(KnowledgeItem.updated_at.desc()).limit(min(max(limit, 1), 100))
        rows = list(self.session.scalars(q))
        items: list[dict[str, Any]] = []
        for row in rows:
            tags = row.tags if isinstance(row.tags, list) else []
            if tag and tag not in tags:
                continue
            items.append(
                {
                    "knowledge_id": str(row.id),
                    "title": row.title,
                    "summary": truncate_summary(row.summary) if row.summary else None,
                    "project": row.project,
                    "tags": tags,
                    "knowledge_type": row.knowledge_type,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                }
            )
        return items

    def get_knowledge_summary(
        self,
        *,
        user_id: UUID,
        knowledge_id: str | None = None,
        pending_id: str | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        raw_id = (knowledge_id or pending_id or "").strip()
        if not raw_id:
            raise DomainError(
                "INVALID_ID",
                "knowledge_id or pending_id is required",
            )
        if knowledge_id and pending_id and knowledge_id.strip() != pending_id.strip():
            raise DomainError(
                "INVALID_ID",
                "knowledge_id and pending_id must refer to the same item when both set",
            )
        try:
            kid = UUID(raw_id)
        except ValueError as exc:
            raise DomainError("ITEM_NOT_FOUND", "invalid id") from exc

        item = self.session.get(KnowledgeItem, kid)
        if item is None or item.user_id != user_id or item.deleted_at is not None:
            raise DomainError("ITEM_NOT_FOUND", "item not found", status_code=404)

        refreshed = False
        if refresh:
            body = self._load_body(item)
            meta = self.km.propose_metadata(text=body, title=item.title)
            item.summary = truncate_summary(meta.get("summary"))
            if meta.get("knowledge_type") and not item.knowledge_type:
                item.knowledge_type = str(meta.get("knowledge_type"))
            item.updated_at = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(item)
            refreshed = True

        return {
            "knowledge_id": str(item.id),
            "title": item.title,
            "status": item.status.value,
            "summary": truncate_summary(item.summary) if item.summary else None,
            "refreshed": refreshed,
        }

    def _load_body(self, item: KnowledgeItem) -> str:
        if not item.body_uri:
            raise DomainError("BODY_MISSING", "proposal has no body")
        from pathlib import Path

        key = item.body_uri
        path = Path(self.settings.blob_root) / key[:2] / key[2:4] / key
        if not path.is_file():
            # fallback flat
            path = Path(self.settings.blob_root) / key
        if not path.is_file():
            raise DomainError("BODY_MISSING", f"blob not found: {key}")
        return path.read_text(encoding="utf-8")
