"""wallet 两表 user_id 维度 RLS 迁移（总纲 §8，轮 25-A 补齐专项）。

088_rls_pilot 因 wallet 按 user_id（非 tenant_id）隔离而跳过；
本迁移补齐 wallet_accounts / wallet_transactions 的 user_id 行级隔离：
- app_user：只能读写本人（current_setting('app.current_user_id')）
- service_role：充值/对账全量旁路

依赖链：down_revision = "088_rls_pilot"（真 PG 链 head）。
回滚：alembic downgrade 088_rls_pilot。
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "089_wallet_user_rls"
down_revision: Union[str, None] = "088_rls_pilot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.wallet_user_rls")

WALLET_TABLES = ("wallet_accounts", "wallet_transactions")


def upgrade() -> None:
    """应用 wallet user_id RLS（PG only，其他方言 noop）。"""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        logger.warning(
            "wallet_user_rls skipped: dialect=%s (only PostgreSQL supported)",
            bind.dialect.name,
        )
        return

    from app.db.rls_policies import (
        WALLET_USER_POLICIES,
        generate_enable_rls_sql,
        generate_policy_sql,
    )

    # 2026-09-05 P0-B：wallet 两表在绿色链上可能未建出（模型表、无建表迁移），
    # 缺表跳过防崩链；角色预建与 088 同理
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
                CREATE ROLE app_user NOLOGIN;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
                CREATE ROLE service_role NOLOGIN;
            END IF;
        END $$;
        """
    )
    existing_tables = set(sa.inspect(bind).get_table_names())
    for table in WALLET_TABLES:
        if table not in existing_tables:
            logger.warning("wallet_user_rls skipped (table absent): %s", table)
            continue
        for sql in generate_enable_rls_sql(table):
            op.execute(sql)
        for policy in WALLET_USER_POLICIES.get(table, []):
            op.execute(generate_policy_sql(policy))
        logger.info("wallet_user_rls applied: %s", table)


def downgrade() -> None:
    """回滚 wallet user_id RLS（PG only）。"""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    from app.db.rls_policies import (
        WALLET_USER_POLICIES,
        generate_disable_rls_sql,
        generate_drop_policy_sql,
    )

    for table in reversed(WALLET_TABLES):
        for policy in reversed(WALLET_USER_POLICIES.get(table, [])):
            op.execute(generate_drop_policy_sql(policy))
        for sql in generate_disable_rls_sql(table):
            op.execute(sql)
        logger.info("wallet_user_rls rolled back: %s", table)
