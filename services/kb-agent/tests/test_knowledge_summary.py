"""Unit tests for KM content overview (≤400 chars) and summary refresh."""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.kb_service import DomainError, KbService
from app.km_client import (
    SUMMARY_MAX_CHARS,
    FakeKmClient,
    build_heuristic_overview,
    truncate_summary,
)
from kb_schema.db import clear_engine_cache, get_engine
from kb_schema.models import KnowledgeItem, KnowledgeStatus, User, UserStatus


def test_should_truncate_summary_to_400_chars():
    long = "测" * 500
    out = truncate_summary(long)
    assert len(out) == SUMMARY_MAX_CHARS


def test_should_build_heuristic_overview_longer_than_title_line():
    body = (
        "第一段介绍系统背景与目标。" * 5
        + "\n\n"
        + "第二段说明模块划分与数据流。" * 5
        + "\n\n"
        + "第三段覆盖索引与检索约束。" * 5
    )
    overview = build_heuristic_overview(body, title="架构说明")
    assert "主题：架构说明" in overview
    assert len(overview) <= SUMMARY_MAX_CHARS
    assert len(overview) >= 80
    assert overview != "架构说明"


def test_should_fake_km_return_overview_not_title_only():
    text = ("段落内容讲私人知识库智能体的架构与 MCP 工具面。" * 8) + "\n\n" + ("检索与提案确认闭环。" * 10)
    meta = FakeKmClient().propose_metadata(text=text, title="kb 架构")
    assert len(meta["summary"]) <= SUMMARY_MAX_CHARS
    assert len(meta["summary"]) > 40
    assert meta["summary"] != "kb 架构"


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


pytestmark_db = pytest.mark.skipif(not _db_available(), reason="Postgres not available")


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


@pytestmark_db
def test_should_store_overview_on_propose_and_list(session_and_user):
    session, user = session_and_user
    body = (
        "kb.agent-mate.ai 是私人知识库智能体。" * 6
        + "\n\n"
        + "包含 kb-agent、kb-rag、管理台与 MCP 门面。" * 6
        + "\n\n"
        + "写入路径为 propose 再 confirm，检索返回可引用片段。" * 6
    )
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient())
        out = svc.propose_ingest(user_id=user.id, text=body, title="架构笔记")
        assert out["summary"]
        assert len(out["summary"]) <= SUMMARY_MAX_CHARS
        assert len(out["summary"]) > 50

        item = session.get(KnowledgeItem, uuid.UUID(out["pending_id"]))
        assert item is not None
        item.status = KnowledgeStatus.confirmed
        session.commit()

        listed = svc.list_knowledge(user_id=user.id)
        assert any(i["knowledge_id"] == out["pending_id"] and i.get("summary") for i in listed)


@pytestmark_db
def test_should_read_and_refresh_knowledge_summary(session_and_user):
    session, user = session_and_user
    body = ("详细正文描述知识库服务边界与租户隔离。" * 12) + "\n\n" + ("向量索引仅在确认后写入。" * 12)
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient())
        proposed = svc.propose_ingest(user_id=user.id, text=body, title="边界说明")
        kid = proposed["pending_id"]

        read = svc.get_knowledge_summary(user_id=user.id, knowledge_id=kid, refresh=False)
        assert read["refreshed"] is False
        assert read["summary"] == proposed["summary"]

        # Shorten stored summary then refresh
        item = session.get(KnowledgeItem, uuid.UUID(kid))
        assert item is not None
        item.summary = "过短"
        session.commit()

        refreshed = svc.get_knowledge_summary(user_id=user.id, pending_id=kid, refresh=True)
        assert refreshed["refreshed"] is True
        assert refreshed["summary"] and len(refreshed["summary"]) > 10
        assert len(refreshed["summary"]) <= SUMMARY_MAX_CHARS
        assert refreshed["summary"] != "过短"


@pytestmark_db
def test_should_reject_summary_without_id(session_and_user):
    session, user = session_and_user
    settings = Settings(use_fake_km=True, blob_root="/tmp")
    svc = KbService(session, settings, km=FakeKmClient())
    with pytest.raises(DomainError) as ei:
        svc.get_knowledge_summary(user_id=user.id)
    assert ei.value.code == "INVALID_ID"
