"""Tests for quota, SSRF, fetch, external search, orchestration, chat."""

from __future__ import annotations

import os
import tempfile
import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app.chat_facade import FakeChatClient, run_chat_loop
from app.config import Settings
from app.kb_service import DomainError, KbService
from app.km_client import FakeKmClient
from app.quota import QuotaLimiter, reset_quota_limiter_for_tests
from app.sources import FixtureSourceAdapter
from app.ssrf import validate_outbound_url
from kb_schema.db import clear_engine_cache, get_engine
from kb_schema.models import KnowledgeItem, User, UserStatus


def test_should_block_loopback_url():
    with pytest.raises(DomainError) as ei:
        validate_outbound_url("http://127.0.0.1/secret")
    assert ei.value.code == "FETCH_BLOCKED"


def test_should_block_non_http_scheme():
    with pytest.raises(DomainError) as ei:
        validate_outbound_url("file:///etc/passwd")
    assert ei.value.code == "FETCH_BLOCKED"


def test_should_rate_limit_when_rpm_exceeded():
    reset_quota_limiter_for_tests()
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    limiter = QuotaLimiter(fetch_rpm=2, external_search_rpm=2, clock=now)
    uid = uuid.uuid4()
    limiter.check_and_consume(uid, "fetch")
    limiter.check_and_consume(uid, "fetch")
    with pytest.raises(DomainError) as ei:
        limiter.check_and_consume(uid, "fetch")
    assert ei.value.code == "RATE_LIMITED"
    clock["t"] = 61.0
    limiter.check_and_consume(uid, "fetch")


def test_should_fixture_external_search_return_candidates():
    adapter = FixtureSourceAdapter()
    hits = adapter.search("合规", top_k=3)
    assert len(hits) == 3
    assert hits[0].url.startswith("https://example.com/")


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
def session_user():
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
def test_should_fetch_url_propose_with_mock_http(session_user):
    session, user = session_user
    html = b"<html><body><p>Fetched public policy text for knowledge base.</p></body></html>"

    class Resp:
        status_code = 200
        url = "https://example.com/policy"
        content = html
        headers = {"content-type": "text/html; charset=utf-8"}

    client = MagicMock(spec=httpx.Client)
    client.get.return_value = Resp()

    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(
            use_fake_km=True,
            blob_root=blob,
            kb_source_use_fixture=True,
            kb_fetch_rpm=100,
        )
        svc = KbService(session, settings, km=FakeKmClient(), http_client=client)
        svc.set_quota_limiter(QuotaLimiter(fetch_rpm=100, external_search_rpm=100))
        out = svc.fetch_url(user_id=user.id, url="https://example.com/policy")
        assert out["proposed"] is True
        assert out.get("pending_id")
        assert out["status"] == "proposed"


@pytestmark_db
def test_should_reject_fetch_private_url(session_user):
    session, user = session_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob, kb_fetch_rpm=100)
        svc = KbService(session, settings, km=FakeKmClient())
        svc.set_quota_limiter(QuotaLimiter(fetch_rpm=100, external_search_rpm=100))
        with pytest.raises(DomainError) as ei:
            svc.fetch_url(user_id=user.id, url="http://127.0.0.1/x")
        assert ei.value.code == "FETCH_BLOCKED"


@pytestmark_db
def test_should_external_search_with_fixture(session_user):
    session, user = session_user
    settings = Settings(
        use_fake_km=True,
        blob_root="/tmp",
        kb_source_use_fixture=True,
        kb_external_search_rpm=100,
    )
    svc = KbService(session, settings, km=FakeKmClient())
    svc.set_quota_limiter(QuotaLimiter(fetch_rpm=100, external_search_rpm=100))
    svc.set_source_adapter(FixtureSourceAdapter())
    out = svc.external_search(user_id=user.id, query="医药代表")
    assert out["count"] >= 1
    assert out["candidates"][0]["url"]


@pytestmark_db
def test_should_source_unavailable_without_fixture_or_key(session_user):
    session, user = session_user
    settings = Settings(
        use_fake_km=True,
        blob_root="/tmp",
        kb_source_use_fixture=False,
        tavily_api_key=None,
        kb_external_search_rpm=100,
    )
    svc = KbService(session, settings, km=FakeKmClient())
    svc.set_quota_limiter(QuotaLimiter(fetch_rpm=100, external_search_rpm=100))
    with pytest.raises(DomainError) as ei:
        svc.external_search(user_id=user.id, query="x")
    assert ei.value.code == "SOURCE_UNAVAILABLE"


@pytestmark_db
def test_should_prefer_internal_when_enough(session_user):
    session, user = session_user

    class FakeSearchSvc(KbService):
        def search(self, *, user_id, query, top_k=8):
            from app.kb_service import SearchHit, SearchOutcome

            return SearchOutcome(
                hits=[
                    SearchHit("a", "c1", "text", 0.9),
                    SearchHit("b", "c2", "text2", 0.8),
                ],
                enough=True,
                reason=None,
            )

        def external_search(self, **kwargs):
            raise AssertionError("external should not be called")

    settings = Settings(use_fake_km=True, blob_root="/tmp", kb_source_use_fixture=True)
    svc = FakeSearchSvc(session, settings, km=FakeKmClient())
    out = svc.search_prefer_internal(user_id=user.id, query="q")
    assert out["used_external"] is False
    assert out["sufficiency"]["enough"] is True


@pytestmark_db
def test_should_call_external_when_not_enough(session_user):
    session, user = session_user

    class FakeSearchSvc(KbService):
        def search(self, *, user_id, query, top_k=8):
            from app.kb_service import SearchOutcome

            return SearchOutcome(hits=[], enough=False, reason="no_hits")

    settings = Settings(use_fake_km=True, blob_root="/tmp", kb_source_use_fixture=True)
    svc = FakeSearchSvc(session, settings, km=FakeKmClient())
    svc.set_quota_limiter(QuotaLimiter(fetch_rpm=100, external_search_rpm=100))
    svc.set_source_adapter(FixtureSourceAdapter())
    out = svc.search_prefer_internal(user_id=user.id, query="稀缺主题")
    assert out["used_external"] is True
    assert out["external_candidates"]


@pytestmark_db
def test_should_chat_loop_with_fake_llm(session_user):
    session, user = session_user

    class FakeSearchSvc(KbService):
        def search(self, *, user_id, query, top_k=8):
            from app.kb_service import SearchHit, SearchOutcome

            return SearchOutcome(
                hits=[SearchHit("k1", "c1", "citation text", 0.5)],
                enough=True,
                reason=None,
            )

    settings = Settings(
        use_fake_km=True,
        blob_root="/tmp",
        chat_facade_enabled=True,
        chat_max_tool_iterations=4,
    )
    svc = FakeSearchSvc(session, settings, km=FakeKmClient())
    out = run_chat_loop(
        svc=svc,
        user_id=user.id,
        messages=[{"role": "user", "content": "库里有什么关于 citation 的内容？"}],
        settings=settings,
        llm=FakeChatClient(),
    )
    assert out["choices"][0]["message"]["content"]
    assert "grounded" in out["choices"][0]["message"]["content"].lower()
