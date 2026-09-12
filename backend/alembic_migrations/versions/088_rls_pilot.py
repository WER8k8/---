"""RLS 试点迁移（总纲 §8 088_rls_pilot，轮 25-A）。

6 张高风险表加 RLS：
- leads（统一为 unified_lead + prospect_lead 两表）
- email_outreach
- content_master
- wallet
- token_ledger（service_role 旁路 + INSERT 强制 tenant_id 校验）
- ubrain_tenant_memory（实际表名 ubrain_accio）

迁移编号：088_rls_pilot（与设计编号一致）

依赖：head=097_meter_events 之前不能跑（按 §15.6 持续无新迁移）
本迁移自 head=097 → 088_rls_pilot_head（虚拟 head）
真实 PG 跑法：alembic upgrade 088_rls_pilot
回滚：alembic downgrade 097_meter_events
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "088_rls_pilot"
# 2026-09-03 二次修正：081-097 全链已在真 PG 逐个真跑生效（见交接记录 §27），
# down_revision 恢复原链 097——不再需要跳链 stamp
down_revision: Union[str, None] = "097"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.rls_pilot")


# RLS 试点的 6 张表（按主键名 + 实际表名）
# 注意：leads 实际是 unified_lead + prospect_lead；ubrain_tenant_memory 实际是 ubrain_accio
# 2026-09-03 真 PG 实战修正：表名对齐模型 __tablename__（原映射是逻辑名，真库里不存在）
PILOT_TABLE_RENAMES = {
    "leads": ("prospect_leads",),
    "email_outreach": ("email_outreachs",),
    "content_master": ("content_masters",),
    # wallet 两表按 user_id 隔离（无 tenant_id 列），tenant_id 模板策略不适用 → 本轮跳过，
    # 留待 25-A 后续专项（user_id 策略）；跳过避免锁死全表
    # "wallet": ("wallet_accounts", "wallet_transactions"),
    "token_ledger": ("token_ledger_entries",),
    "ubrain_tenant_memory": ("ubrain_tenant_memory",),
}


def upgrade() -> None:
    """应用 RLS 到 6 张表（PG only，SQLite 直接 noop）。"""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        logger.warning(
            "rls_pilot skipped: dialect=%s (only PostgreSQL supported)",
            bind.dialect.name,
        )
        return

    from app.db.rls_policies import (
        DEFAULT_POLICIES,
        generate_enable_rls_sql,
        generate_policy_sql,
    )

    # 2026-09-05 P0-B：策略引用的组角色幂等预建（PG 无 CREATE ROLE IF NOT EXISTS）。
    # 活库/RLS 验证库此前手工建过 app_user/service_role；绿色链全新库必须自建，
    # 否则 CREATE POLICY ... TO app_user 报 UndefinedObject 崩链。NOLOGIN 组角色，
    # 仅作 set role 目标，不引入登录面。
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
    for logical_name, table_names in PILOT_TABLE_RENAMES.items():
        for table in table_names:
            # 2026-09-05 P0-B：RLS 目标表可能尚未在绿色链上建出
            # （prospect_leads 等模型表全链无建表迁移，活库靠 create_all），
            # 缺表时跳过该表而非崩整条链
            if table not in existing_tables:
                logger.warning("rls_pilot skipped (table absent): %s", table)
                continue
            # 1) 启用 RLS
            for sql in generate_enable_rls_sql(table):
                op.execute(sql)
            # 2) 创建策略（按 logical_name 查 DEFAULT_POLICIES 复用模板）
            for policy in DEFAULT_POLICIES.get(logical_name, []):
                # 策略模板的 table 字段是 logical_name，要替换为实际 table
                real_policy_sql = generate_policy_sql(
                    policy.__class__(
                        table=table,
                        policy_name=policy.policy_name,
                        tenant_id_column=policy.tenant_id_column,
                        operation=policy.operation,
                        role=policy.role,
                        using_expr=policy.using_expr,
                        with_check_expr=policy.with_check_expr,
                        description=policy.description,
                    )
                )
                op.execute(real_policy_sql)
            logger.info("rls_pilot applied: %s", table)


def downgrade() -> None:
    """回滚 RLS（PG only，SQLite 直接 noop）。"""
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    from app.db.rls_policies import (
        DEFAULT_POLICIES,
        generate_disable_rls_sql,
        generate_drop_policy_sql,
    )

    for logical_name, table_names in reversed(list(PILOT_TABLE_RENAMES.items())):
        for table in table_names:
            # 1) drop 策略——策略是按物理表名建的，drop 也要用物理表名
            #    （2026-09-03 实测 bug 修复：policy.template.table 是逻辑名，
            #     直接 drop 逻辑名会漏删真实策略，downgrade 后残留 5 条）
            for policy in reversed(DEFAULT_POLICIES.get(logical_name, [])):
                real_policy = policy.__class__(
                    table=table,
                    policy_name=policy.policy_name,
                    tenant_id_column=policy.tenant_id_column,
                    operation=policy.operation,
                    role=policy.role,
                    using_expr=policy.using_expr,
                    with_check_expr=policy.with_check_expr,
                    description=policy.description,
                )
                op.execute(generate_drop_policy_sql(real_policy))
            # 2) disable
            for sql in generate_disable_rls_sql(table):
                op.execute(sql)
            logger.info("rls_pilot rolled back: %s", table)
