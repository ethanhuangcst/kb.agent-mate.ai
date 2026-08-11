"""Index gate: proposed items must never be indexed (rag-index-02)."""

from __future__ import annotations

from typing import Any

from kb_schema.models import KnowledgeItem, KnowledgeStatus


class IndexGuardError(ValueError):
    """Raised when indexing a non-confirmed knowledge item."""

    code = "RAG_INDEX_NOT_CONFIRMED"


def assert_indexable(item: KnowledgeItem | dict[str, Any]) -> None:
    """Raise if ``item`` is not confirmed / is deleted.

    Accepts a ``KnowledgeItem`` ORM row or a plain dict with ``status`` / ``deleted_at``.
    """
    if isinstance(item, KnowledgeItem):
        status = item.status
        deleted_at = item.deleted_at
        knowledge_id = str(item.id)
    else:
        status = item.get("status")
        deleted_at = item.get("deleted_at")
        knowledge_id = str(item.get("id") or item.get("knowledge_id") or "?")

    status_value = status.value if isinstance(status, KnowledgeStatus) else str(status or "")

    if deleted_at is not None:
        raise IndexGuardError(
            f"refusing to index deleted knowledge_id={knowledge_id} (rag-index-02)"
        )
    if status_value != KnowledgeStatus.confirmed.value:
        raise IndexGuardError(
            f"refusing to index knowledge_id={knowledge_id} with status={status_value!r}; "
            "only confirmed items may be indexed (rag-index-02)"
        )
