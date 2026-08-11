"""Unit tests for item detail / update / soft-delete (agent-item-01/02)."""

from __future__ import annotations

import os
import tempfile
import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.kb_service import DomainError, KbService
from app.km_client import FakeKmClient
from kb_schema.db import clear_engine_cache, get_engine
from kb_schema.models import KnowledgeItem, KnowledgeStatus, User, UserStatus


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
    other = User(display_name=f"O-{uuid.uuid4().hex[:8]}", status=UserStatus.active)
    session.add_all([user, other])
    session.commit()
    yield session, user, other
    session.query(KnowledgeItem).filter(
        KnowledgeItem.user_id.in_([user.id, other.id])
    ).delete(synchronize_session=False)
    session.query(User).filter(User.id.in_([user.id, other.id])).delete(
        synchronize_session=False
    )
    session.commit()
    session.close()


def _mock_rag_ok() -> httpx.Client:
    client = MagicMock(spec=httpx.Client)

    def post(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "/internal/delete" in url:
            resp.text = '{"deleted":true}'
            resp.json.return_value = {"deleted": True, "removed_points": 1}
        else:
            resp.text = "{}"
            resp.json.return_value = {}
        return resp

    client.post.side_effect = post
    return client


def test_should_get_item_detail_when_owned(session_and_user):
    session, user, _other = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient(), http_client=_mock_rag_ok())
        proposed = svc.propose_ingest(
            user_id=user.id,
            text="条目详情测试正文内容足够长。" * 8,
            title="详情标题",
            project="p1",
            tags=["t1"],
        )
        kid = proposed["pending_id"]
        detail = svc.get_item(user_id=user.id, item_id=kid)
        assert detail["knowledge_id"] == kid
        assert detail["title"] == "详情标题"
        assert detail["status"] == "proposed"
        assert detail["project"] == "p1"
        assert detail["tags"] == ["t1"]
        assert detail["summary"]


def test_should_reject_get_item_when_other_user(session_and_user):
    session, user, other = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient(), http_client=_mock_rag_ok())
        proposed = svc.propose_ingest(
            user_id=user.id,
            text="他户隔离测试正文。" * 10,
            title="私有",
        )
        with pytest.raises(DomainError) as ei:
            svc.get_item(user_id=other.id, item_id=proposed["pending_id"])
        assert ei.value.code == "ITEM_NOT_FOUND"


def test_should_update_metadata_when_patch(session_and_user):
    session, user, _other = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient(), http_client=_mock_rag_ok())
        proposed = svc.propose_ingest(
            user_id=user.id,
            text="更新元数据测试正文。" * 10,
            title="旧标题",
            project="old",
        )
        kid = proposed["pending_id"]
        updated = svc.update_item(
            user_id=user.id,
            item_id=kid,
            title="新标题",
            project="new-proj",
            tags=["a", "b"],
        )
        assert updated["title"] == "新标题"
        assert updated["project"] == "new-proj"
        assert updated["tags"] == ["a", "b"]


def test_should_soft_delete_and_hide_from_list(session_and_user):
    session, user, _other = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        http = _mock_rag_ok()
        svc = KbService(session, settings, km=FakeKmClient(), http_client=http)
        proposed = svc.propose_ingest(
            user_id=user.id,
            text="软删测试正文内容。" * 12,
            title="待删",
        )
        kid = proposed["pending_id"]
        item = session.get(KnowledgeItem, uuid.UUID(kid))
        assert item is not None
        item.status = KnowledgeStatus.confirmed
        session.commit()

        out = svc.soft_delete_item(user_id=user.id, item_id=kid)
        assert out["deleted"] is True
        assert out["status"] == "deleted"

        listed = svc.list_knowledge(user_id=user.id)
        assert all(i["knowledge_id"] != kid for i in listed)

        with pytest.raises(DomainError) as ei:
            svc.get_item(user_id=user.id, item_id=kid)
        assert ei.value.code == "ITEM_NOT_FOUND"

        # RAG delete called
        assert any("/internal/delete" in str(c.args[0]) for c in http.post.call_args_list)
