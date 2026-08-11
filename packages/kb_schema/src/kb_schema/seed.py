"""Bootstrap helpers."""

from __future__ import annotations

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kb_schema.models import AdminUser


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def ensure_seed_admin(session: Session) -> AdminUser | None:
    """Create default admin/admin if no admin_users exist.

    Returns the created user, or ``None`` if admins already exist.
    """
    count = session.scalar(select(func.count()).select_from(AdminUser)) or 0
    if count > 0:
        return None

    admin = AdminUser(
        username="admin",
        email=None,
        display_name="Admin",
        password_hash=hash_password("admin"),
        must_change_password=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin
