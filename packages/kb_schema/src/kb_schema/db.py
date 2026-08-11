"""Engine and session factory helpers."""

from __future__ import annotations

import os
from collections.abc import Callable
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return url


@lru_cache(maxsize=8)
def get_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    """Return a cached SQLAlchemy engine for ``url`` (or ``DATABASE_URL``)."""
    database_url = url or _database_url()
    connect_args: dict = {}
    engine_kwargs: dict = {"echo": echo, "future": True}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # Shared in-memory DB across connections (tests).
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
    engine_kwargs["connect_args"] = connect_args
    return create_engine(database_url, **engine_kwargs)


def get_session(url: str | None = None, *, echo: bool = False) -> sessionmaker[Session]:
    """Return a ``sessionmaker`` bound to the engine for ``url`` / ``DATABASE_URL``."""
    engine = get_engine(url, echo=echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def clear_engine_cache() -> None:
    """Drop cached engines (tests / URL rotation)."""
    get_engine.cache_clear()


SessionFactory = Callable[[], Session]
