"""合并所有 head — 统一迁移链

Revision ID: 058_merge_all_heads
Revises: 016_add_ai_config_tables, 050_paperclip, 057_add_missing_indexes
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa

revision = "058_merge_all_heads"
down_revision = ("016_add_ai_config_tables", "050_paperclip", "057_add_missing_indexes")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
