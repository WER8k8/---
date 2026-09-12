"""全链路归因 + 客户发现关联

Revision ID: 054_attribution_fields
Revises: 053_product_bilingual_faq
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

revision = "054_attribution_fields"
down_revision = "053_product_bilingual_faq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 询盘归因字段
    op.add_column("inquiries", sa.Column("source_url", sa.String(1000), nullable=True, comment="来源页面完整 URL"))
    op.add_column("inquiries", sa.Column("source_keyword", sa.String(300), nullable=True, comment="搜索关键词"))
    op.add_column("inquiries", sa.Column("ai_search_engine", sa.String(50), nullable=True, comment="AI 搜索引擎来源"))
    op.add_column("inquiries", sa.Column("attribution_channel", sa.String(50), nullable=True, comment="归因渠道"))
    op.add_column("inquiries", sa.Column("attribution_data", sa.Text, nullable=True, comment="归因详情 JSON"))
    op.add_column("inquiries", sa.Column("customer_finder_id", sa.String(36), nullable=True, index=True, comment="关联 Customer Finder 结果"))
    op.create_index("ix_inquiries_attribution_channel", "inquiries", ["attribution_channel"])


def downgrade() -> None:
    op.drop_index("ix_inquiries_attribution_channel", "inquiries")
    op.drop_column("inquiries", "customer_finder_id")
    op.drop_column("inquiries", "attribution_data")
    op.drop_column("inquiries", "attribution_channel")
    op.drop_column("inquiries", "ai_search_engine")
    op.drop_column("inquiries", "source_keyword")
    op.drop_column("inquiries", "source_url")
