"""Import batch + organize unit tests (MVP-3)."""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.import_extract import extract_text
from app.kb_service import DomainError, KbService
from app.km_client import FakeKmClient
from kb_schema.db import clear_engine_cache, get_engine
from kb_schema.models import ImportBatch, KnowledgeItem, KnowledgeStatus, User, UserStatus


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
    user = User(display_name=f"Imp-{uuid.uuid4().hex[:8]}", status=UserStatus.active)
    session.add(user)
    session.commit()
    yield session, user
    session.query(KnowledgeItem).filter(KnowledgeItem.user_id == user.id).delete()
    session.query(ImportBatch).filter(ImportBatch.user_id == user.id).delete()
    session.query(User).filter(User.id == user.id).delete()
    session.commit()
    session.close()


def test_should_reject_unsupported_extension():
    out = extract_text("x.exe", b"MZ")
    assert out.text is None
    assert out.error_code == "IMPORT_FILE_REJECTED"


def test_should_extract_md():
    out = extract_text("a.md", b"# Hello\n\nworld")
    assert out.text and "Hello" in out.text


def test_should_create_batch_proposals_without_confirm(session_and_user):
    session, user = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient())
        uid = uuid.uuid4().hex[:8]
        out = svc.create_import_batch(
            user_id=user.id,
            files=[
                (f"n1-{uid}.md", f"# Note one {uid}\n\nbody".encode()),
                (f"n2-{uid}.txt", f"plain {uid}".encode()),
                ("bad.exe", b"nope"),
            ],
            default_project="mvp3",
            default_tags=["batch"],
        )
        assert out["batch_id"]
        assert len(out["proposals"]) == 2
        assert any(f["code"] == "IMPORT_FILE_REJECTED" for f in out["failures"])
        for p in out["proposals"]:
            assert p["status"] == KnowledgeStatus.proposed.value


def test_should_reject_too_many_files(session_and_user):
    session, user = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob, kb_import_max_files_per_batch=1)
        svc = KbService(session, settings, km=FakeKmClient())
        with pytest.raises(DomainError) as ei:
            svc.create_import_batch(
                user_id=user.id,
                files=[("a.md", b"a"), ("b.md", b"b")],
            )
        assert ei.value.code == "IMPORT_LIMIT_EXCEEDED"


def test_should_confirm_all_viable(session_and_user, monkeypatch):
    session, user = session_and_user

    class FakeResp:
        status_code = 200

        def text(self):  # pragma: no cover
            return ""

    class FakeHttp:
        def post(self, *a, **k):
            return FakeResp()

        def close(self):
            pass

    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient(), http_client=FakeHttp())
        uid = uuid.uuid4().hex[:8]
        created = svc.create_import_batch(
            user_id=user.id,
            files=[(f"c-{uid}.md", f"confirm me {uid}".encode())],
        )
        conf = svc.confirm_import_batch(
            user_id=user.id,
            batch_id=created["batch_id"],
            confirm_all_viable=True,
        )
        assert len(conf["confirmed"]) == 1
        assert conf["status"] == "completed"


def test_should_organize_retag_apply(session_and_user):
    session, user = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient())
        uid = uuid.uuid4().hex[:8]
        prop = svc.propose_ingest(user_id=user.id, text=f"org body {uid}", project="p1")

        class FakeResp:
            status_code = 200

        class FakeHttp:
            def post(self, *a, **k):
                return FakeResp()

            def close(self):
                pass

        svc2 = KbService(session, settings, km=FakeKmClient(), http_client=FakeHttp())
        svc2.confirm_ingest(user_id=user.id, pending_id=prop["pending_id"])
        out = svc2.organize(
            user_id=user.id,
            action="retag",
            project="p1",
            apply=True,
            instruction="project:mvp3-org",
        )
        assert out["applied"]
        assert "organized" in (out["applied"][0].get("tags") or [])


def test_should_reject_organize_strategy_instruction(session_and_user):
    session, user = session_and_user
    with tempfile.TemporaryDirectory() as blob:
        settings = Settings(use_fake_km=True, blob_root=blob)
        svc = KbService(session, settings, km=FakeKmClient())
        with pytest.raises(DomainError) as ei:
            svc.organize(
                user_id=user.id,
                action="summarize",
                instruction="请给出投放策略",
            )
        assert ei.value.code == "OUT_OF_SCOPE_BUSINESS_REASONING"
