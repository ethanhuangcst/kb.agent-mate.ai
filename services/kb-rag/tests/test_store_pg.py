"""rag-store-01: Blob + PostgreSQL knowledge_items metadata."""

from __future__ import annotations

import os
import uuid

import pytest

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
)

from kb_schema.db import clear_engine_cache, get_engine, get_session  # noqa: E402
from kb_schema.models import KnowledgeItem, KnowledgeStatus, User, UserStatus  # noqa: E402
from app.blob_store import BlobStore  # noqa: E402
from app.indexer_guard import IndexGuardError, assert_indexable  # noqa: E402


def _db_available() -> bool:
    try:
        clear_engine_cache()
        engine = get_engine(os.environ["DATABASE_URL"])
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not available on :5434")


def test_blob_and_pg_metadata_roundtrip(tmp_path):
    clear_engine_cache()
    store = BlobStore(tmp_path)
    body = b"full knowledge body for store-01"
    blob_key = store.put(body)

    SessionLocal = get_session(os.environ["DATABASE_URL"])
    session = SessionLocal()
    user = User(display_name=f"store-{uuid.uuid4().hex[:6]}", status=UserStatus.active)
    session.add(user)
    session.flush()
    item = KnowledgeItem(
        user_id=user.id,
        content_hash=blob_key,
        title="Store test",
        summary="meta",
        body_uri=f"blob://{blob_key}",
        status=KnowledgeStatus.confirmed,
    )
    session.add(item)
    session.commit()
    item_id = item.id
    user_id = user.id
    session.close()

    assert store.get(blob_key) == body

    session = SessionLocal()
    loaded = session.get(KnowledgeItem, item_id)
    assert loaded is not None
    assert loaded.body_uri == f"blob://{blob_key}"
    assert loaded.is_indexable is True
    session.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).delete()
    session.query(User).filter(User.id == user_id).delete()
    session.commit()
    session.close()


def test_proposed_item_not_indexable_via_guard():
    with pytest.raises(IndexGuardError):
        assert_indexable({"id": "x", "status": "proposed", "deleted_at": None})
