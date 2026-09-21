"""P0-5/P0-8 — inquiries 表新增独立 UTM 列 + priority_score

背景：
- P0-5：原归因仅落 source_utm（序列化 blob），无法按 utm_source/campaign 检索与
  聚合；补齐独立列后归因报表可直接用 SQL 过滤。
- P0-8：线索分配此前纯轮询（least-loaded），不看线索价值；新增 priority_score
  列，评分驱动分配排序，高价值线索在销售队列中获得更高权重。

依赖：down_revision = 116_normalize_lead_enum_case
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "117_add_inquiry_utm_priority_columns"
down_revision: Union[str, None] = "116_normalize_lead_enum_case"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("inquiries", sa.Column("utm_source", sa.String(length=200), nullable=True))
    op.add_column("inquiries", sa.Column("utm_medium", sa.String(length=120), nullable=True))
    op.add_column("inquiries", sa.Column("utm_campaign", sa.String(length=200), nullable=True))
    op.add_column("inquiries", sa.Column("utm_content", sa.String(length=200), nullable=True))
    op.add_column("inquiries", sa.Column("utm_term", sa.String(length=200), nullable=True))
    op.add_column(
        "inquiries",
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_inquiries_utm_source", "inquiries", ["utm_source"])
    op.create_index("ix_inquiries_utm_medium", "inquiries", ["utm_medium"])
    op.create_index("ix_inquiries_utm_campaign", "inquiries", ["utm_campaign"])


def downgrade() -> None:
    op.drop_index("ix_inquiries_utm_campaign", table_name="inquiries")
    op.drop_index("ix_inquiries_utm_medium", table_name="inquiries")
    op.drop_index("ix_inquiries_utm_source", table_name="inquiries")
    op.drop_column("inquiries", "utm_term")
    op.drop_column("inquiries", "utm_content")
    op.drop_column("inquiries", "utm_campaign")
    op.drop_column("inquiries", "utm_medium")
    op.drop_column("inquiries", "utm_source")
    op.drop_column("inquiries", "priority_score")
