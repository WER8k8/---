"""104: orders/quotes 回填 tenant_id（ADR-001 第 1 组，经 UserTenant 可推导部分）。

回填规则（可推导）：merchant_id（交易对手用户）→ user_tenants 中该用户的 active 租户。
无法推导部分（历史用户无租户归属）保持 NULL + 审计日志（留产品/DBA 裁决）。
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "104_backfill_tenant_id_from_usertenant"
down_revision: Union[str, Sequence[str], None] = "102_tenant_unification_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.backfill_tenant_id")


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        # PostgreSQL: UPDATE from user_tenants 子查询
        for table in ("orders", "quotes"):
            result = bind.execute(sa.text(f"""
                UPDATE {table} SET tenant_id = (
                    SELECT ut.tenant_id FROM user_tenants ut
                    WHERE ut.user_id = {table}.merchant_id
                    AND ut.is_active = TRUE
                    LIMIT 1
                )
                WHERE tenant_id IS NULL
                  AND EXISTS (
                    SELECT 1 FROM user_tenants ut
                    WHERE ut.user_id = {table}.merchant_id
                    AND ut.is_active = TRUE
                  )
            """))
            n = result.rowcount
            logger.info("%s: %d 行回填 tenant_id", table, n if n >= 0 else '?')
    else:
        # SQLite 不支持 UPDATE...FROM（3.33+ 支持但兼容起见用子查询）
        for table in ("orders", "quotes"):
            try:
                result = bind.execute(sa.text(f"""
                    UPDATE {table} SET tenant_id = (
                        SELECT ut.tenant_id FROM user_tenants ut
                        WHERE ut.user_id = {table}.merchant_id
                        AND ut.is_active = 1
                        LIMIT 1
                    )
                    WHERE tenant_id IS NULL
                      AND EXISTS (
                        SELECT 1 FROM user_tenants ut
                        WHERE ut.user_id = {table}.merchant_id
                        AND ut.is_active = 1
                      )
                """))
                logger.info("%s: SQLite UPDATE 执行", table)
            except Exception as e:
                logger.warning("%s: SQLite UPDATE 失败（留 NULL）: %s", table, e)


def downgrade() -> None:
    logger.warning("downgrade 104: 无法精确反回填；建议不 downgrade 此迁移")
