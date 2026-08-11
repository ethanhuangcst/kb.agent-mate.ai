"""Unit tests for KbService domain rules (scope / hash / propose)."""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.kb_service import DomainError, KbService, content_hash
from app.km_client import FakeKmClient
from kb_schema.db import clear_engine_cache, get_engine
from kb_schema.models import KnowledgeItem, KnowledgeStatus, User, UserStatus


def test_should_hash_normalize_whitespace():
    assert content_hash("a  b") == content_hash("a b")


def _db_available() -> bool:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
    )
    try:
        clear_engine_cache()
        engine = get_engine(url)
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="Postgres not available")


@pytest.fixture()
def session_and_user():
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://kb:kb_dev_password@127.0.0.1:5434/kb_agent",
    )
    clear_engine_cache()
    engine = get_engine(url)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    user = User(display_name=f"U-{uuid.uuid4().hex[:8]}", status=UserStatus.active)
    session.add(user)
    session.commit()
    yield session, user
    session.query(KnowledgeItem).filter(KnowledgeItem.user_id == user.id).delete()
    session.query(User).filter(User.id == user.id).delete()
    session.commit()
    session.close()


def test_should_reject_auto_ingest_when_flag_set(session_and_user):
    session, user = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob, database_url=os.environ.get("DATABASE_URL", ""))
        svc = KbService(session, settings, km=FakeKmClient())
        with pytest.raises(DomainError) as ei:
            svc.propose_ingest(user_id=user.id, text="hello", auto_ingest=True)
        assert ei.value.code == "OUT_OF_SCOPE_AUTO_INGEST"


def test_should_create_proposed_without_indexing(session_and_user):
    session, user = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient())
        out = svc.propose_ingest(
            user_id=user.id,
            text="Unique paste about widget pricing " + uuid.uuid4().hex,
            title="Widget note",
            tags=["mvp2"],
        )
        assert out["status"] == KnowledgeStatus.proposed.value
        assert out["duplicate_hint"] is False
        item = session.get(KnowledgeItem, uuid.UUID(out["pending_id"]))
        assert item is not None
        assert item.status == KnowledgeStatus.proposed
        assert item.is_indexable is False
