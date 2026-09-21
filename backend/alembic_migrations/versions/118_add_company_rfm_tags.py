"""P1-8 — companies 表新增标签/RFM 分段列

背景：
- P1-8 需要「RFM 分层 + 标签体系 + ABM 账号聚合」，但 companies 表此前没有任何
  标签承载列，标签算出来无处落库 → 运营无法按标签筛选/圈人。
- 本次补齐 4 列：tags(JSON 数组文本) / rfm_segment(分层) / rfm_code(如 "543")
  / rfm_updated_at(计算时间，便于判断数据新鲜度)。
- rfm_segment 建索引：运营最常用的筛选维度是按分层圈人。

依赖：down_revision = 117_add_inquiry_utm_priority_columns
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "118_add_company_rfm_tags"
down_revision: Union[str, None] = "117_add_inquiry_utm_priority_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("tags", sa.Text(), nullable=True))
    op.add_column("companies", sa.Column("rfm_segment", sa.String(length=30), nullable=True))
    op.add_column("companies", sa.Column("rfm_code", sa.String(length=10), nullable=True))
    op.add_column(
        "companies", sa.Column("rfm_updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_companies_rfm_segment", "companies", ["rfm_segment"])


def downgrade() -> None:
    op.drop_index("ix_companies_rfm_segment", table_name="companies")
    op.drop_column("companies", "rfm_updated_at")
    op.drop_column("companies", "rfm_code")
    op.drop_column("companies", "rfm_segment")
    op.drop_column("companies", "tags")
