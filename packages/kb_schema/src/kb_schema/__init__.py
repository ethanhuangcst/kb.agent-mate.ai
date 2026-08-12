"""Shared schema package for kb.agent-mate.ai."""

from kb_schema.base import Base
from kb_schema.db import get_engine, get_session
from kb_schema.models import (
    AdminInvite,
    AdminStatus,
    AdminUser,
    ApiKey,
    ImportBatch,
    ImportBatchStatus,
    KnowledgeItem,
    KnowledgeStatus,
    PasswordResetToken,
    User,
)
from kb_schema.seed import ensure_seed_admin

__all__ = [
    "Base",
    "AdminUser",
    "AdminStatus",
    "AdminInvite",
    "PasswordResetToken",
    "User",
    "ApiKey",
    "ImportBatch",
    "ImportBatchStatus",
    "KnowledgeItem",
    "KnowledgeStatus",
    "get_engine",
    "get_session",
    "ensure_seed_admin",
]
