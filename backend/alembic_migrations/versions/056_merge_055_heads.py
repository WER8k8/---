"""合并 055 双头

Revision ID: 056_merge_055_heads
Revises: 055_content_feedback_checks, 055_industry_insights
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

revision = "056_merge_055_heads"
down_revision = ("055_content_feedback_checks", "055_industry_insights")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
