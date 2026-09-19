"""订单/支付状态大小写归一 + 枚举词表对齐

背景（2026-09-19 冒烟）：
- OrderStatus/PaymentStatus 为 str Enum，业务/API/测试统一使用 value（小写）
  如 pending / deposit_received / in_production。
- 历史 SQLAlchemy 默认按枚举 Name（大写）写库，部分代码路径又直接写 value，
  导致 orders.status 混有 CONFIRMED 与 pending；读回时 LookupError → GET /api/v1/orders 500。
- PG 侧 order_status_enum 还曾混入 _TRANSITIONS 等污染标签，且缺 7 步闭环新状态。

本迁移：
1. 将 orders.status / orders.payment_status 全部归一为小写 value；
2. 若存在原生 enum 类型，重建为与 Python 枚举 value 一致的词表。

依赖：down_revision = 114_p0_core_business_tables（当前单 head）。
回滚：alembic downgrade 114_p0_core_business_tables（仅恢复 head 指针，数据不回滚大小写）。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "115_normalize_order_status_case"
down_revision: Union[str, None] = "114_p0_core_business_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 与 app.models.enums.OrderStatus / PaymentStatus 的 value 对齐
_ORDER_STATUS_VALUES = [
    "draft",
    "pending",
    "paid",
    "confirmed",
    "deposit_received",
    "in_production",
    "shipped",
    "final_payment_received",
    "completed",
    "cancelled",
    "refunded",
    "partial_refunded",
]
_PAYMENT_STATUS_VALUES = [
    "pending",
    "processing",
    "paid",
    "failed",
    "refunded",
    "cancelled",
]

# 历史 Name 大写 → value 小写；含个别脏值兜底
_ORDER_CASE_MAP = {
    "DRAFT": "draft",
    "PENDING": "pending",
    "PAID": "paid",
    "CONFIRMED": "confirmed",
    "DEPOSIT_RECEIVED": "deposit_received",
    "IN_PRODUCTION": "in_production",
    "SHIPPED": "shipped",
    "FINAL_PAYMENT_RECEIVED": "final_payment_received",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled",
    "REFUNDED": "refunded",
    "PARTIAL_REFUNDED": "partial_refunded",
}
_PAYMENT_CASE_MAP = {
    "PENDING": "pending",
    "PROCESSING": "processing",
    "PAID": "paid",
    "FAILED": "failed",
    "REFUNDED": "refunded",
    "CANCELLED": "cancelled",
}


def _enum_exists(conn, type_name: str) -> bool:
    return bool(
        conn.execute(
            sa.text(
                "SELECT 1 FROM pg_type t WHERE t.typname = :n"
            ),
            {"n": type_name},
        ).scalar()
    )


def _normalize_column(conn, table: str, column: str, valid: list[str], case_map: dict[str, str]) -> None:
    # 1) 大写 Name → 小写 value
    for src, dst in case_map.items():
        conn.execute(
            sa.text(f'UPDATE "{table}" SET "{column}" = :dst WHERE "{column}" = :src'),
            {"dst": dst, "src": src},
        )
    # 2) 大小写不敏感归一到合法小写 value
    for val in valid:
        conn.execute(
            sa.text(
                f'UPDATE "{table}" SET "{column}" = :dst '
                f'WHERE lower("{column}") = :low AND "{column}" <> :dst'
            ),
            {"dst": val, "low": val},
        )
    # 3) 仍非法的值落到 pending（订单/支付默认可解释状态），避免读库炸
    placeholders = ", ".join(f":v{i}" for i in range(len(valid)))
    params = {f"v{i}": v for i, v in enumerate(valid)}
    params["fallback"] = "pending"
    conn.execute(
        sa.text(
            f'UPDATE "{table}" SET "{column}" = :fallback '
            f'WHERE "{column}" IS NOT NULL AND "{column}" NOT IN ({placeholders})'
        ),
        params,
    )


def _rebuild_enum(conn, type_name: str, values: list[str], owner_table: str, owner_cols: list[str]) -> None:
    if not _enum_exists(conn, type_name):
        return
    tmp = f"{type_name}_new"
    conn.execute(sa.text(f'DROP TYPE IF EXISTS "{tmp}" CASCADE'))
    labels = ", ".join(f"'{v}'" for v in values)
    conn.execute(sa.text(f'CREATE TYPE "{tmp}" AS ENUM ({labels})'))
    for col in owner_cols:
        # 列可能是 varchar 或旧 enum；统一经 text 再转新 enum
        conn.execute(
            sa.text(
                f'ALTER TABLE "{owner_table}" '
                f'ALTER COLUMN "{col}" TYPE "{tmp}" USING ("{col}"::text)::"{tmp}"'
            )
        )
    conn.execute(sa.text(f'DROP TYPE IF EXISTS "{type_name}" CASCADE'))
    conn.execute(sa.text(f'ALTER TYPE "{tmp}" RENAME TO "{type_name}"'))


def upgrade() -> None:
    conn = op.get_bind()
    _normalize_column(conn, "orders", "status", _ORDER_STATUS_VALUES, _ORDER_CASE_MAP)
    _normalize_column(conn, "orders", "payment_status", _PAYMENT_STATUS_VALUES, _PAYMENT_CASE_MAP)
    _rebuild_enum(conn, "order_status_enum", _ORDER_STATUS_VALUES, "orders", ["status"])
    _rebuild_enum(conn, "payment_status_enum", _PAYMENT_STATUS_VALUES, "orders", ["payment_status"])


def downgrade() -> None:
    # 数据大小写归一不可逆；仅保持 head 可回指
    pass
