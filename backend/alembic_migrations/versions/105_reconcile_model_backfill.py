"""105: 兜底合流——迁移链尾部用模型元数据补建缺失表（幂等）。

Revision ID: 105_reconcile_model_backfill
Revises: 104_backfill_tenant_id_from_usertenant
Create Date: 2026-09-05

背景（2026-09-05 P0-B 绿色链实测）：迁移链历史长期靠 create_all 掩盖，绿色链
001→104 跑通后仅产出 141 张表，而模型 Base.metadata 有 200 张——88 张模型表
（admin_*、campaigns、companies 等核心业务表）全链无建表迁移，纯迁移建库
缺表不可用；反过来 29 张迁移表模型已删除。

本迁移在链尾调用 Base.metadata.create_all（幂等：只建缺失表，绝不改/删已存表）：
- 全新环境：alembic upgrade heads 一步得到与模型一致的 200+ 表
- 存量环境（活库 create_all 建）：create_all 全部跳过，零改动
- 差异表（29 张迁移遗留表）保留不动，由后续治理迁移裁决去留

这是把"alembic 链"与"create_all 模型"两条建库路径合流的务实收口；
后续新表应回到"模型变更即 autogenerate 迁移"的正常轨道（101 已开对齐先例）。
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "105_reconcile_model_backfill"
down_revision: Union[str, None] = "104_backfill_tenant_id_from_usertenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.reconcile_model_backfill")


def upgrade() -> None:
    bind = op.get_bind()
    # 注册全部模型后再 create_all；幂等——已存在的表一律跳过
    import app.models  # noqa: F401
    from app.core.database import Base

    before = set(sa.inspect(bind).get_table_names())
    Base.metadata.create_all(bind=bind)
    after = set(sa.inspect(bind).get_table_names())
    created = sorted(after - before)
    logger.info(
        "reconcile_model_backfill: tables before=%d after=%d created=%d %s",
        len(before), len(after), len(created), created[:20],
    )


def downgrade() -> None:
    # 兜底建的表不回删：无法区分哪些表由本迁移创建（create_all 幂等无记录），
    # 且删除业务表风险不可接受。回滚本迁移仅表示放弃后续兜底，不撤销已建表。
    pass
