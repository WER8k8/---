"""inquiries.phone 放宽为可空（修公开询盘的 email-only 500）。

背景（2026-09-14，做租户官网「采购 Agent 可撮合出口」时实测暴露）：
- `POST /api/v1/inquiries` 的入参校验明确允许"手机号或邮箱至少填一个"
  （routes/inquiries.py `require_contact_channel`），随后把 `phone=None`
  交给 `InquiriesUnifiedService.create_public_lead` 落库；
- 但 `inquiries.phone` 一直是 `nullable=False`，于是**只留邮箱的公开询盘必然
  撞 NotNullViolation 抛 500**。B2B 买家（以及代客提问的采购 agent）常常只给
  企业邮箱不给电话，这条路径等于对一半的潜在线索是断的。
- 此前未暴露是因为站点表单默认要求电话，agent 出口没有表单约束，一打就中。

修法：只放宽列约束，不改任何写读代码——下游对 phone 仅用于等值/ilike 过滤与
序列化，None 天然安全；存量行不受影响。

依赖链：down_revision = 112_add_fact_kernel_json（当前单 head）。
回滚：alembic downgrade 112_add_fact_kernel_json（会把已有 NULL 电话行反撞约束，
属预期行为，回滚前需先补电话）。
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "113_inquiries_phone_nullable"
down_revision: Union[str, None] = "112_add_fact_kernel_json"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("inquiries", "phone", existing_type=sa.String(length=50), nullable=True)
