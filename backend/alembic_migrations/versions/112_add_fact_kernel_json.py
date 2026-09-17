"""母版事实内核落库（全平台内容中台 蓝图 §2 / 缺口 #8 持久化）

背景（2026-09-13）：
- `content_masters` 此前只有文案列，FactKernel 只在发布请求运行时算一次即丢弃，
  导致同一母版多次发布事实层漂移、下游形态无法回溯「当时用了哪些硬事实」。
- 新增 `fact_kernel_json`（JSON，可空）持久化内核快照；存量行保持 NULL，零回滚风险。

依赖链：down_revision = 111_order_trade_fields（当前单 head）。
回滚：alembic downgrade 111_order_trade_fields。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "112_add_fact_kernel_json"
down_revision: Union[str, None] = "111_order_trade_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_masters",
        sa.Column("fact_kernel_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_masters", "fact_kernel_json")
