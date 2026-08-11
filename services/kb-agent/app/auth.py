"""Bearer API key authentication."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from kb_schema.db import get_session
from kb_schema.models import ApiKey, ApiKeyStatus, User, UserStatus

from app.config import Settings, get_settings


@dataclass
class AuthContext:
    user_id: UUID
    api_key_id: UUID
    key_prefix: str


def hash_api_key(raw_key: str, pepper: str) -> str:
    return hashlib.sha256(f"{pepper}{raw_key}".encode("utf-8")).hexdigest()


def get_db(settings: Settings = Depends(get_settings)) -> Iterator[Session]:
    SessionLocal = get_session(settings.database_url)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def require_bearer(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED"})
    raw = authorization.split(" ", 1)[1].strip()
    if not raw:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED"})
    digest = hash_api_key(raw, settings.api_key_pepper)
    row = db.execute(
        select(ApiKey, User).join(User, User.id == ApiKey.user_id).where(ApiKey.key_hash == digest)
    ).first()
    if row is None:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED"})
    api_key, user = row
    if api_key.status != ApiKeyStatus.active:
        raise HTTPException(status_code=401, detail={"code": "KEY_REVOKED"})
    if user.status != UserStatus.active:
        raise HTTPException(status_code=401, detail={"code": "USER_DISABLED"})
    return AuthContext(user_id=user.id, api_key_id=api_key.id, key_prefix=api_key.key_prefix)
