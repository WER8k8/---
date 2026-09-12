"""行业洞察表 — 跨租户匿名行业洞察聚合

Revision ID: 055_industry_insights
Revises: 054_attribution_fields
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

revision = "055_industry_insights"
down_revision = "054_attribution_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "industry_insights",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("industry", sa.String(100), nullable=False, comment="行业分类"),
        sa.Column("pattern_type", sa.String(50), nullable=False, comment="模式类型: tactic / benchmark / content_style / keyword_cluster"),
        sa.Column("pattern_data", sa.Text, nullable=False, comment="模式详情 JSON"),
        sa.Column("success_score", sa.Float, nullable=False, server_default="0.0", comment="成功评分 0~1"),
        sa.Column("sample_count", sa.Integer, nullable=False, server_default="0", comment="样本租户数"),
        sa.Column("source_tenant_hash", sa.String(64), nullable=True, comment="来源租户 SHA-256 匿名哈希"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_industry_insights_industry", "industry_insights", ["industry"])
    op.create_index("ix_industry_insights_pattern_type", "industry_insights", ["pattern_type"])
    op.create_index("ix_industry_insights_success_score", "industry_insights", ["success_score"])


def downgrade() -> None:
    op.drop_index("ix_industry_insights_success_score", "industry_insights")
    op.drop_index("ix_industry_insights_pattern_type", "industry_insights")
    op.drop_index("ix_industry_insights_industry", "industry_insights")
    op.drop_table("industry_insights")
