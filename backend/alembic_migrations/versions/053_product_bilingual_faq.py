"""产品双语字段 + FAQ 表

Revision ID: 053_product_bilingual_faq
Revises: 052_soft_delete
Create Date: 2026-07-19
"""
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "053_product_bilingual_faq"
down_revision = "052_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 产品英文字段
    op.add_column("products", sa.Column("name_en", sa.String(200), nullable=True, comment="English product name"))
    op.add_column("products", sa.Column("subtitle_en", sa.String(300), nullable=True, comment="English subtitle"))
    op.add_column("products", sa.Column("description_en", sa.Text, nullable=True, comment="English description"))
    op.add_column("products", sa.Column("technical_params_en", sa.Text, nullable=True, comment="English technical parameters"))
    op.add_column("products", sa.Column("advantages_en", sa.Text, nullable=True, comment="English advantages"))
    op.add_column("products", sa.Column("application_scenarios_en", sa.Text, nullable=True, comment="English application scenarios"))
    op.add_column("products", sa.Column("meta_title_en", sa.String(200), nullable=True, comment="English SEO title"))
    op.add_column("products", sa.Column("meta_description_en", sa.String(500), nullable=True, comment="English SEO description"))

    # 产品 FAQ 表
    op.create_table(
        "product_faqs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("product_id", _uuid_col(), sa.ForeignKey("products.id"), nullable=False, index=True),
        sa.Column("question_zh", sa.String(500), nullable=False, comment="中文问题"),
        sa.Column("answer_zh", sa.Text, nullable=False, comment="中文回答"),
        sa.Column("question_en", sa.String(500), nullable=True, comment="English question"),
        sa.Column("answer_en", sa.Text, nullable=True, comment="English answer"),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("product_faqs")
    op.drop_column("products", "name_en")
    op.drop_column("products", "subtitle_en")
    op.drop_column("products", "description_en")
    op.drop_column("products", "technical_params_en")
    op.drop_column("products", "advantages_en")
    op.drop_column("products", "application_scenarios_en")
    op.drop_column("products", "meta_title_en")
    op.drop_column("products", "meta_description_en")
