"""Shared schema package for kb.agent-mate.ai."""

from kb_schema.base import Base
from kb_schema.db import get_engine, get_session
from kb_schema.models import AdminUser, ApiKey, KnowledgeItem, User
from kb_schema.seed import ensure_seed_admin

__all__ = [
    "Base",
    "AdminUser",
    "User",
    "ApiKey",
    "KnowledgeItem",
    "get_engine",
    "get_session",
    "ensure_seed_admin",
]
