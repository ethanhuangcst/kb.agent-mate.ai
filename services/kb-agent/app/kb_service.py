"""Domain service shared by REST and MCP facades."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.km_client import KmClient, build_km_client, truncate_summary
from kb_schema.models import ImportBatch, ImportBatchStatus, KnowledgeItem, KnowledgeStatus


class DomainError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        degrade_hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.degrade_hint = degrade_hint


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
        self._quota = None  # lazy
        self._source_adapter = None

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
        notes: str | None = None,
        batch_id: UUID | None = None,
        source_filename: str | None = None,
    ) -> dict[str, Any]:
        if auto_ingest or skip_confirm:
            raise DomainError(
                "OUT_OF_SCOPE_AUTO_INGEST",
                "Auto-ingest / skip confirm is not allowed; use propose then confirm.",
            )
        from app.scope_guard import check_business_scope

        # Scope-01/02: intent in title/notes (not body — body may document strategies).
        check_business_scope(title, notes)
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
                "batch_id": str(existing.batch_id) if existing.batch_id else None,
                "source_filename": existing.source_filename,
            }

        meta = self.km.propose_metadata(text=body, title=title)
        overview = truncate_summary(meta.get("summary"))
        blob_key = digest
        root = self.settings.blob_root

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
            batch_id=batch_id,
            source_filename=(source_filename[:512] if source_filename else None),
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
            "batch_id": str(item.batch_id) if item.batch_id else None,
            "source_filename": item.source_filename,
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

    def get_item(self, *, user_id: UUID, item_id: str) -> dict[str, Any]:
        try:
            kid = UUID(item_id.strip())
        except ValueError as exc:
            raise DomainError("ITEM_NOT_FOUND", "invalid id", status_code=404) from exc
        item = self.session.get(KnowledgeItem, kid)
        if item is None or item.user_id != user_id or item.deleted_at is not None:
            raise DomainError("ITEM_NOT_FOUND", "item not found", status_code=404)
        tags = item.tags if isinstance(item.tags, list) else []
        return {
            "knowledge_id": str(item.id),
            "title": item.title,
            "summary": truncate_summary(item.summary) if item.summary else None,
            "project": item.project,
            "tags": tags,
            "knowledge_type": item.knowledge_type,
            "status": item.status.value,
            "source_filename": item.source_filename,
            "batch_id": str(item.batch_id) if item.batch_id else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }

    def update_item(
        self,
        *,
        user_id: UUID,
        item_id: str,
        title: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        knowledge_type: str | None = None,
    ) -> dict[str, Any]:
        try:
            kid = UUID(item_id.strip())
        except ValueError as exc:
            raise DomainError("ITEM_NOT_FOUND", "invalid id", status_code=404) from exc
        item = self.session.get(KnowledgeItem, kid)
        if item is None or item.user_id != user_id or item.deleted_at is not None:
            raise DomainError("ITEM_NOT_FOUND", "item not found", status_code=404)
        if title is not None:
            title_s = title.strip()
            if not title_s:
                raise DomainError("INVALID_INPUT", "title must not be empty")
            item.title = title_s[:512]
        if project is not None:
            item.project = project.strip() or None
        if tags is not None:
            item.tags = list(tags)
        if knowledge_type is not None:
            item.knowledge_type = knowledge_type.strip() or None
        item.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(item)
        return self.get_item(user_id=user_id, item_id=str(item.id))

    def soft_delete_item(self, *, user_id: UUID, item_id: str) -> dict[str, Any]:
        try:
            kid = UUID(item_id.strip())
        except ValueError as exc:
            raise DomainError("ITEM_NOT_FOUND", "invalid id", status_code=404) from exc
        item = self.session.get(KnowledgeItem, kid)
        if item is None or item.user_id != user_id or item.deleted_at is not None:
            raise DomainError("ITEM_NOT_FOUND", "item not found", status_code=404)
        now = datetime.now(timezone.utc)
        item.status = KnowledgeStatus.deleted
        item.deleted_at = now
        item.updated_at = now
        self.session.commit()
        self._rag_delete(user_id=user_id, knowledge_id=str(item.id))
        return {"knowledge_id": str(item.id), "status": "deleted", "deleted": True}

    def _rag_delete(self, *, user_id: UUID, knowledge_id: str) -> None:
        try:
            resp = self._client().post(
                f"{self.settings.rag_base_url.rstrip('/')}/internal/delete",
                headers={"X-Service-Token": self.settings.rag_service_token},
                json={"user_id": str(user_id), "knowledge_id": knowledge_id},
            )
        except httpx.HTTPError as exc:
            raise DomainError("RAG_UNAVAILABLE", str(exc), status_code=502) from exc
        if resp.status_code not in (200, 204):
            raise DomainError("RAG_ERROR", resp.text[:500], status_code=502)

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

    def create_import_batch(
        self,
        *,
        user_id: UUID,
        files: list[tuple[str, bytes]],
        default_project: str | None = None,
        default_tags: list[str] | None = None,
    ) -> dict[str, Any]:
        from app.import_extract import extract_text, is_allowed_filename

        max_files = self.settings.kb_import_max_files_per_batch
        max_file = self.settings.kb_import_max_bytes_per_file
        max_batch = self.settings.kb_import_max_bytes_per_batch

        if not files:
            raise DomainError("IMPORT_FILE_REJECTED", "at least one file is required")
        if len(files) > max_files:
            raise DomainError(
                "IMPORT_LIMIT_EXCEEDED",
                f"too many files ({len(files)} > {max_files})",
            )
        total = sum(len(b) for _, b in files)
        if total > max_batch:
            raise DomainError(
                "IMPORT_LIMIT_EXCEEDED",
                f"batch too large ({total} > {max_batch} bytes)",
            )
        for name, data in files:
            if len(data) > max_file:
                raise DomainError(
                    "IMPORT_LIMIT_EXCEEDED",
                    f"file too large: {name} ({len(data)} > {max_file} bytes)",
                )

        batch = ImportBatch(
            id=uuid4(),
            user_id=user_id,
            status=ImportBatchStatus.open,
            default_project=default_project,
            default_tags=list(default_tags or []),
            failures=[],
        )
        self.session.add(batch)
        self.session.flush()

        proposals: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        tags = list(default_tags or [])

        for name, data in files:
            if not is_allowed_filename(name):
                failures.append(
                    {
                        "filename": name,
                        "code": "IMPORT_FILE_REJECTED",
                        "message": "unsupported extension; allowed: .md .txt .pdf",
                    }
                )
                continue
            extracted = extract_text(name, data)
            if extracted.text is None:
                failures.append(
                    {
                        "filename": name,
                        "code": extracted.error_code or "IMPORT_FILE_REJECTED",
                        "message": extracted.message or "extract failed",
                    }
                )
                continue
            try:
                out = self.propose_ingest(
                    user_id=user_id,
                    text=extracted.text,
                    title=Path(name).stem,
                    project=default_project,
                    tags=tags or None,
                    batch_id=batch.id,
                    source_filename=name,
                )
                proposals.append({**out, "filename": name})
            except DomainError as exc:
                failures.append(
                    {
                        "filename": name,
                        "code": exc.code,
                        "message": exc.message,
                    }
                )

        batch.failures = failures
        self.session.commit()
        self.session.refresh(batch)
        return {
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "proposals": proposals,
            "failures": failures,
        }

    def get_import_batch(self, *, user_id: UUID, batch_id: str) -> dict[str, Any]:
        try:
            bid = UUID(batch_id)
        except ValueError as exc:
            raise DomainError("BATCH_NOT_FOUND", "invalid batch_id") from exc
        batch = self.session.get(ImportBatch, bid)
        if batch is None or batch.user_id != user_id:
            raise DomainError("BATCH_NOT_FOUND", "batch not found", status_code=404)

        rows = list(
            self.session.scalars(
                select(KnowledgeItem).where(
                    KnowledgeItem.user_id == user_id,
                    KnowledgeItem.batch_id == bid,
                    KnowledgeItem.deleted_at.is_(None),
                )
            )
        )
        proposals = [
            {
                "pending_id": str(r.id),
                "status": r.status.value,
                "title": r.title,
                "summary": r.summary,
                "source_filename": r.source_filename,
                "duplicate_hint": False,
            }
            for r in rows
            if r.status == KnowledgeStatus.proposed
        ]
        confirmed = [
            {
                "knowledge_id": str(r.id),
                "status": r.status.value,
                "title": r.title,
                "source_filename": r.source_filename,
            }
            for r in rows
            if r.status == KnowledgeStatus.confirmed
        ]
        return {
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "default_project": batch.default_project,
            "default_tags": batch.default_tags if isinstance(batch.default_tags, list) else [],
            "proposals": proposals,
            "confirmed": confirmed,
            "failures": batch.failures if isinstance(batch.failures, list) else [],
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "finished_at": batch.finished_at.isoformat() if batch.finished_at else None,
        }

    def confirm_import_batch(
        self,
        *,
        user_id: UUID,
        batch_id: str,
        pending_ids: list[str] | None = None,
        confirm_all_viable: bool = False,
    ) -> dict[str, Any]:
        try:
            bid = UUID(batch_id)
        except ValueError as exc:
            raise DomainError("BATCH_NOT_FOUND", "invalid batch_id") from exc
        batch = self.session.get(ImportBatch, bid)
        if batch is None or batch.user_id != user_id:
            raise DomainError("BATCH_NOT_FOUND", "batch not found", status_code=404)

        q = select(KnowledgeItem).where(
            KnowledgeItem.user_id == user_id,
            KnowledgeItem.batch_id == bid,
            KnowledgeItem.status == KnowledgeStatus.proposed,
            KnowledgeItem.deleted_at.is_(None),
        )
        rows = list(self.session.scalars(q))
        if confirm_all_viable:
            targets = rows
        elif pending_ids:
            wanted = {p.strip() for p in pending_ids if p and p.strip()}
            targets = [r for r in rows if str(r.id) in wanted]
            missing = wanted - {str(r.id) for r in targets}
            if missing:
                raise DomainError(
                    "PENDING_NOT_FOUND",
                    f"pending not in batch: {', '.join(sorted(missing)[:5])}",
                    status_code=404,
                )
        else:
            raise DomainError(
                "INVALID_INPUT",
                "provide pending_ids or confirm_all_viable=true",
            )

        confirmed: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for row in targets:
            try:
                out = self.confirm_ingest(user_id=user_id, pending_id=str(row.id))
                confirmed.append(out)
            except DomainError as exc:
                errors.append({"pending_id": str(row.id), "code": exc.code, "message": exc.message})

        remaining = self.session.scalar(
            select(KnowledgeItem.id).where(
                KnowledgeItem.batch_id == bid,
                KnowledgeItem.status == KnowledgeStatus.proposed,
                KnowledgeItem.deleted_at.is_(None),
            ).limit(1)
        )
        if remaining is None:
            batch.status = ImportBatchStatus.completed
            batch.finished_at = datetime.now(timezone.utc)
            self.session.commit()

        return {
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "confirmed": confirmed,
            "errors": errors,
        }

    def organize(
        self,
        *,
        user_id: UUID,
        action: str,
        project: str | None = None,
        tag: str | None = None,
        knowledge_type: str | None = None,
        instruction: str | None = None,
        apply: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        from app.scope_guard import check_business_scope

        check_business_scope(instruction)
        action_n = (action or "").strip().lower()
        if action_n not in {"summarize", "retag", "reclassify"}:
            raise DomainError("INVALID_INPUT", "action must be summarize|retag|reclassify")

        items = self.list_knowledge(
            user_id=user_id,
            project=project,
            tag=tag,
            knowledge_type=knowledge_type,
            limit=limit,
        )
        suggestions = self.km.organize_suggestions(
            action=action_n,
            items=items,
            instruction=instruction,
        )
        applied: list[dict[str, Any]] = []
        if apply:
            for sug in suggestions:
                kid = sug.get("knowledge_id")
                if not kid:
                    continue
                try:
                    uid = UUID(str(kid))
                except ValueError:
                    continue
                row = self.session.get(KnowledgeItem, uid)
                if row is None or row.user_id != user_id or row.deleted_at is not None:
                    continue
                if row.status != KnowledgeStatus.confirmed:
                    continue
                if "project" in sug and sug["project"] is not None:
                    row.project = str(sug["project"])[:256] or None
                if "tags" in sug and isinstance(sug["tags"], list):
                    row.tags = [str(t)[:64] for t in sug["tags"][:20]]
                if "knowledge_type" in sug and sug["knowledge_type"]:
                    row.knowledge_type = str(sug["knowledge_type"])[:64]
                row.updated_at = datetime.now(timezone.utc)
                applied.append(
                    {
                        "knowledge_id": str(row.id),
                        "project": row.project,
                        "tags": row.tags if isinstance(row.tags, list) else [],
                        "knowledge_type": row.knowledge_type,
                    }
                )
            self.session.commit()

        return {
            "action": action_n,
            "apply": apply,
            "suggestions": suggestions,
            "applied": applied,
        }

    def _quota_limiter(self):
        if self._quota is None:
            from app.quota import QuotaLimiter

            self._quota = QuotaLimiter(
                fetch_rpm=self.settings.kb_fetch_rpm,
                external_search_rpm=self.settings.kb_external_search_rpm,
            )
        return self._quota

    def set_quota_limiter(self, limiter) -> None:
        self._quota = limiter

    def _get_source_adapter(self):
        if self._source_adapter is None:
            from app.sources import build_source_adapter

            self._source_adapter = build_source_adapter(
                tavily_api_key=self.settings.tavily_api_key,
                use_fixture=self.settings.kb_source_use_fixture,
                http_client=self._http,
            )
        return self._source_adapter

    def set_source_adapter(self, adapter) -> None:
        self._source_adapter = adapter

    def fetch_url(
        self,
        *,
        user_id: UUID,
        url: str,
        title: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
        propose: bool = True,
    ) -> dict[str, Any]:
        self._quota_limiter().check_and_consume(user_id, "fetch")
        from app.fetch_url import fetch_url_text

        text = fetch_url_text(url, client=self._client())
        derived_title = title or url.strip()[:200]
        if not propose:
            return {"url": url, "text": text, "title": derived_title, "proposed": False}
        out = self.propose_ingest(
            user_id=user_id,
            text=text,
            title=derived_title,
            project=project,
            tags=tags,
            notes=f"fetched:{url}",
        )
        out["url"] = url
        out["proposed"] = True
        return out

    def external_search(
        self,
        *,
        user_id: UUID,
        query: str,
        project: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        q = (query or "").strip()
        if not q:
            raise DomainError("INVALID_INPUT", "query is required")
        self._quota_limiter().check_and_consume(user_id, "external_search")
        adapter = self._get_source_adapter()
        candidates = [c.as_dict() for c in adapter.search(q, top_k=top_k)]
        return {
            "query": q,
            "project": project,
            "candidates": candidates,
            "count": len(candidates),
        }

    def search_prefer_internal(
        self,
        *,
        user_id: UUID,
        query: str,
        top_k: int = 8,
        force_external: bool = False,
        project: str | None = None,
    ) -> dict[str, Any]:
        internal = self.search(user_id=user_id, query=query, top_k=top_k)
        payload: dict[str, Any] = {
            "hits": [h.__dict__ for h in internal.hits],
            "sufficiency": {"enough": internal.enough, "reason": internal.reason},
            "external_candidates": [],
            "used_external": False,
        }
        if internal.enough and not force_external:
            return payload
        external = self.external_search(
            user_id=user_id,
            query=query,
            project=project,
            top_k=min(top_k, 8),
        )
        payload["external_candidates"] = external.get("candidates") or []
        payload["used_external"] = True
        return payload
