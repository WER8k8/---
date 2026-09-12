"""RLS 第二批补齐（技术债 G.4）：5 张试点物理表现在已存在但缺行级安全。

背景（2026-09-11 真 PG 实测）：
- 088_rls_pilot / 089_wallet_user_rls 在当年跑时，prospect_leads / email_outreachs /
  token_ledger_entries / wallet_accounts / wallet_transactions 尚未建出（模型表靠
  create_all，108_missing_business_tables 才补建），缺表被跳过 → 这 5 表至今仍
  rls=False、无策略；而 content_masters / payment_orders / ubrain_tenant_memory
  已在 088/100 下带 RLS。
- 应用库用户 youding 已是 app_user、service_role、pg_read_all_data、pg_write_all_data
  成员，且现有 3 表已证明 ENABLE+FORCE 下仍可见行 → FORCE 风险解除。

设计（照抄 100_rls_batch1_trade_core 的稳健写法，避免 ::uuid 强转在 varchar/uuid
分裂时 CREATE POLICY 报错）：
- 每张表：app_user 隔离策略（tenant 维度用 tenant_id::text；wallet 用 user_id varchar）
  + service_role 全量 bypass（USING true）→ 应用侧（youding ∈ service_role）任何上下文
  恒可读，租户隔离仅对 app_user 生效。
- token_ledger_entries 是全局账本：service_role 全量旁路 + app_user 仅 INSERT（含 tenant 校验）。
- 幂等：CREATE POLICY 前先 DROP POLICY IF EXISTS；缺表跳过（绿色链安全）。

依赖链：down_revision = 108_missing_business_tables（当前单 head）。
回滚：alembic downgrade 108_missing_business_tables。
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "109_rls_batch2_pilot_reapply"
down_revision: Union[str, None] = "108_missing_business_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.rls_batch2_pilot_reapply")

# 每表策略规格：(table, tenant_isolation_column_or_None, user_isolation_column_or_None, service_ledger)
# - tenant_col 非空 → app_user 走 tenant_id::text 隔离 + service_role bypass
# - user_col  非空 → app_user 走 user_id（varchar，无 cast）隔离 + service_role bypass
# - service_ledger=True → service_role 全量 + app_user 仅 INSERT（token 账本专用）
_TARGETS = (
    ("prospect_leads", "tenant_id", None, False),
    ("email_outreachs", "tenant_id", None, False),
    ("wallet_accounts", None, "user_id", False),
    ("wallet_transactions", None, "user_id", False),
    ("token_ledger_entries", "tenant_id", None, True),
)


def _policy_names_for(table: str, tenant_col, user_col, service_ledger) -> list[str]:
    names: list[str] = []
    if service_ledger:
        names += ["token_ledger_service_only", "token_ledger_tenant_insert"]
        return names
    if tenant_col:
        names += [f"{table}_tenant_isolation", f"{table}_service_bypass"]
    if user_col:
        names += [f"{table}_user_isolation", f"{table}_service_bypass"]
    return names


def _apply_one(bind, table: str, tenant_col, user_col, service_ledger) -> None:
    # 幂等：先 drop 本表可能已存在的策略（含 088/089 遗留命名）
    for name in _policy_names_for(table, tenant_col, user_col, service_ledger):
        op.execute(f"DROP POLICY IF EXISTS {name} ON {table};")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    if service_ledger:
        # 全局账本：service_role 全量旁路
        op.execute(
            f"CREATE POLICY token_ledger_service_only ON {table}\n"
            "  FOR ALL\n"
            "  TO service_role\n"
            "  USING (true)\n"
            "  WITH CHECK (true);"
        )
        # app_user 仅可 INSERT，且强制写入当前租户（INSERT 策略无 USING 子句）
        op.execute(
            f"CREATE POLICY token_ledger_tenant_insert ON {table}\n"
            "  FOR INSERT\n"
            "  TO app_user\n"
            "  WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id'));"
        )
        return

    if tenant_col:
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table}\n"
            "  FOR ALL\n"
            "  TO app_user\n"
            f"  USING ({tenant_col}::text = current_setting('app.current_tenant_id'))\n"
            f"  WITH CHECK ({tenant_col}::text = current_setting('app.current_tenant_id'));"
        )
    if user_col:
        # wallet 两表 user_id 是 varchar(64)，不做 ::uuid cast（088 实战教训）
        op.execute(
            f"CREATE POLICY {table}_user_isolation ON {table}\n"
            "  FOR ALL\n"
            "  TO app_user\n"
            f"  USING ({user_col} = current_setting('app.current_user_id'))\n"
            f"  WITH CHECK ({user_col} = current_setting('app.current_user_id'));"
        )
    # 每表都补 service_role 全量旁路 → 应用侧恒可读
    op.execute(
        f"CREATE POLICY {table}_service_bypass ON {table}\n"
        "  FOR ALL\n"
        "  TO service_role\n"
        "  USING (true)\n"
        "  WITH CHECK (true);"
    )


def upgrade() -> None:
    """补齐 5 张试点物理表的 RLS（PG only，其他方言 noop）。"""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        logger.warning(
            "rls_batch2 skipped: dialect=%s (only PostgreSQL supported)",
            bind.dialect.name,
        )
        return

    # 角色幂等预建（同 088/089/100）
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
    # 列型校验：只对真实存在对应隔离列的表出策略，避免 CREATE POLICY 引用不存在列
    inspector = sa.inspect(bind)
    for table, tenant_col, user_col, service_ledger in _TARGETS:
        if table not in existing_tables:
            logger.warning("rls_batch2 skipped (table absent): %s", table)
            continue
        col_names = {c["name"] for c in inspector.get_columns(table)}
        if tenant_col and tenant_col not in col_names:
            logger.warning("rls_batch2 skipped (no %s col): %s", tenant_col, table)
            continue
        if user_col and user_col not in col_names:
            logger.warning("rls_batch2 skipped (no %s col): %s", user_col, table)
            continue
        _apply_one(bind, table, tenant_col, user_col, service_ledger)
        logger.info("rls_batch2 applied: %s", table)


def downgrade() -> None:
    """回滚 5 表 RLS（PG only，逆序 drop + disable）。"""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    existing_tables = set(sa.inspect(bind).get_table_names())
    for table, tenant_col, user_col, service_ledger in reversed(_TARGETS):
        if table not in existing_tables:
            continue
        for name in _policy_names_for(table, tenant_col, user_col, service_ledger):
            op.execute(f"DROP POLICY IF EXISTS {name} ON {table};")
        op.execute("ALTER TABLE %s NO FORCE ROW LEVEL SECURITY;" % table)
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        logger.info("rls_batch2 rolled back: %s", table)
