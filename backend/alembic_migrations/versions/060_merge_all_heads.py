"""合并所有 head — 统一迁移链

Revision ID: 060_merge_all_heads
Revises: 059, 081
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa

revision = "060_merge_all_heads"
down_revision = ("059", "081")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
