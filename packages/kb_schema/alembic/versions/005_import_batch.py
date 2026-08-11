"""ImportBatch + knowledge_items.batch_id / source_filename (MVP-3 import).

Revision ID: 005_import_batch
Revises: 004_admin_invite_reset
Create Date: 2026-08-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_import_batch"
down_revision: Union[str, None] = "004_admin_invite_reset"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("default_project", sa.String(length=256), nullable=True),
        sa.Column(
            "default_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "failures",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_batches_user_id", "import_batches", ["user_id"])
    op.create_index("ix_import_batches_status", "import_batches", ["status"])

    op.add_column("knowledge_items", sa.Column("batch_id", sa.Uuid(), nullable=True))
    op.add_column("knowledge_items", sa.Column("source_filename", sa.String(length=512), nullable=True))
    op.create_foreign_key(
        "fk_knowledge_items_batch_id",
        "knowledge_items",
        "import_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_knowledge_items_batch_id", "knowledge_items", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_items_batch_id", table_name="knowledge_items")
    op.drop_constraint("fk_knowledge_items_batch_id", "knowledge_items", type_="foreignkey")
    op.drop_column("knowledge_items", "source_filename")
    op.drop_column("knowledge_items", "batch_id")
    op.drop_index("ix_import_batches_status", table_name="import_batches")
    op.drop_index("ix_import_batches_user_id", table_name="import_batches")
    op.drop_table("import_batches")
