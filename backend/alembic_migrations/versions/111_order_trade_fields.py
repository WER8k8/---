"""订单外贸履约字段（P/I 定金核销 + CI/箱单套打数据）

背景（2026-09-13 外贸业务组审计）：
- 现有 orders 表仅有 shipping_address/method/tracking，缺 7 步闭环「④定金核销」「⑥发运单证(CI/箱单)」
  所需字段：无贸易术语、付款条款、定金比例/金额，无毛净重/体积/唛头/箱号/提单号/起运-目的港。
- 新增 12 个全 nullable 列，存量订单零回滚风险；供卖家后台按订单填写以支撑 P/I、CI、箱单套打。

依赖链：down_revision = 110_add_order_access_token（当前单 head）。
回滚：alembic downgrade 110_add_order_access_token。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "111_order_trade_fields"
down_revision: Union[str, None] = "110_add_order_access_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("incoterms", sa.String(10)),
    ("payment_terms", sa.String(50)),
    ("deposit_ratio", sa.Numeric(5, 2)),
    ("deposit_amount", sa.Numeric(10, 2)),
    ("port_of_loading", sa.String(100)),
    ("port_of_discharge", sa.String(100)),
    ("gross_weight", sa.Numeric(12, 3)),
    ("net_weight", sa.Numeric(12, 3)),
    ("volume", sa.Numeric(12, 3)),
    ("shipping_marks", sa.Text()),
    ("container_no", sa.String(50)),
    ("bl_number", sa.String(50)),
]


def upgrade() -> None:
    for name, type_ in _COLS:
        op.add_column("orders", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLS):
        op.drop_column("orders", name)