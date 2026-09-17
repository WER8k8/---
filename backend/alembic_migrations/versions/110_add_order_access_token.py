"""订单买家访问令牌列（order-token 鉴权）

背景（2026-09-13 实测）：
- 遗留 /api/v1/orders 读接口无鉴权、写接口仅全局 HMAC → IDOR 越权（匿名可枚举全站订单）。
- 新增 Order.access_token 列：创建订单时下发 64 位 hex 令牌；买家凭令牌
  （X-Order-Token 头 / order_token 参数）查询、取消、确认收货自己的订单；
  卖家/管理员走登录态（Bearer）。存量订单 access_token 为 NULL，
  需卖家后台补发令牌后买家方可访问（无令牌匿名请求一律 404/400/403）。

依赖链：down_revision = 109_rls_batch2_pilot_reapply（当前单 head）。
回滚：alembic downgrade 109_rls_batch2_pilot_reapply。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "110_add_order_access_token"
down_revision: Union[str, None] = "109_rls_batch2_pilot_reapply"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("access_token", sa.String(length=64), nullable=True))
    op.create_index("ix_orders_access_token", "orders", ["access_token"])


def downgrade() -> None:
    op.drop_index("ix_orders_access_token", table_name="orders")
    op.drop_column("orders", "access_token")
