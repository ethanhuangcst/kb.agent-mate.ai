"""Tests for kb_schema seed and models."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from kb_schema import Base, ensure_seed_admin, get_engine, get_session
from kb_schema.db import clear_engine_cache
from kb_schema.models import AdminUser, KnowledgeItem, KnowledgeStatus
from kb_schema.seed import verify_password


@pytest.fixture()
def session(tmp_path: Path):
    clear_engine_cache()
    url = f"sqlite+pysqlite:///{tmp_path / 'test.db'}"
    os.environ["DATABASE_URL"] = url
    engine = get_engine(url)
    Base.metadata.create_all(engine)
    Session = get_session(url)
    with Session() as s:
        yield s
    clear_engine_cache()


def test_ensure_seed_admin_creates_once(session):
    created = ensure_seed_admin(session)
    assert created is not None
    assert created.username == "admin"
    assert created.must_change_password is True
    assert verify_password("admin", created.password_hash)

    again = ensure_seed_admin(session)
    assert again is None
    rows = session.scalars(select(AdminUser)).all()
    assert len(rows) == 1


def test_knowledge_proposed_not_indexable():
    item = KnowledgeItem(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        content_hash="abc",
        title="t",
        status=KnowledgeStatus.proposed,
    )
    assert item.is_indexable is False
    item.status = KnowledgeStatus.confirmed
    assert item.is_indexable is True
