"""Add key_ciphertext to api_keys for admin view (ADR-007).

Revision ID: 003_api_key_ciphertext
Revises: 002_knowledge_tags
Create Date: 2026-08-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_api_key_ciphertext"
down_revision: Union[str, None] = "002_knowledge_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("key_ciphertext", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "key_ciphertext")
