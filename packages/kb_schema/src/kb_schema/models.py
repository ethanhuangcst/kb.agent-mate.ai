"""MVP-1 SQLAlchemy models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from kb_schema.base import Base


class UserStatus(str, enum.Enum):
    active = "active"
    disabled = "disabled"


class ApiKeyStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class KnowledgeStatus(str, enum.Enum):
    """Item lifecycle. ``proposed`` must never be indexed/searchable (rag-index-02)."""

    proposed = "proposed"
    confirmed = "confirmed"
    deleted = "deleted"


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_admin_users_username"),
        UniqueConstraint("email", name="uq_admin_users_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=False, length=32),
        nullable=False,
        default=UserStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="user")
    knowledge_items: Mapped[list[KnowledgeItem]] = relationship(back_populates="user")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[ApiKeyStatus] = mapped_column(
        Enum(ApiKeyStatus, name="api_key_status", native_enum=False, length=32),
        nullable=False,
        default=ApiKeyStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="api_keys")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    knowledge_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[KnowledgeStatus] = mapped_column(
        Enum(KnowledgeStatus, name="knowledge_status", native_enum=False, length=32),
        nullable=False,
        default=KnowledgeStatus.proposed,
        index=True,
    )
    project: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="knowledge_items")

    @property
    def is_indexable(self) -> bool:
        """Only confirmed items may be vector-indexed (rag-index-02)."""
        return self.status == KnowledgeStatus.confirmed and self.deleted_at is None
