"""RLS 试点策略（总纲 §8 088_rls_pilot，轮 25-A）。

目标：6 张高风险表加 RLS + 连接池 checkout/checkin 钩子，P2 剩余一半。

设计原则：
- 策略生成与数据库无关：所有 SQL 在 Python 端拼装，调用方传入 SQLAlchemy
  Connection/Inspector 即可执行
- 策略以 tenant_id 列为主键：每张表有 tenant_id 列时强制 WHERE tenant_id = current_setting
- 缺 tenant_id 列的表（如 token_ledger 全局账本）走"白名单 service_role 旁路"模式
- 每个策略提供 enable / disable / verify 三种操作

本轮 25-A 只生成 + 应用策略，不做真实连接池钩子（连接池钩子随 25-B 在 DB 层补齐）。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, Optional

logger = logging.getLogger("uj-admin.rls_pilot")


# 6 张高风险表（按 §8 088_rls_pilot 路线）
RLS_PILOT_TABLES: tuple[str, ...] = (
    "leads",                  # 线索（含 unified_lead + prospect_lead 两个具体表）
    "email_outreach",         # 邮件触达
    "content_master",         # 内容主表
    "wallet",                 # 钱包
    "token_ledger",           # Token 账本
    "ubrain_tenant_memory",   # 租户记忆
)

# 逻辑名 → 物理表名映射（2026-09-03 真 PG 实测修正：对齐模型 __tablename__）
# unified_lead 无 ORM 表（纯 dataclass）；wallet 按 user_id 隔离，本轮跳过
RLS_PILOT_TABLE_MAPPING: dict[str, tuple[str, ...]] = {
    "leads": ("prospect_leads",),
    "email_outreach": ("email_outreachs",),
    "content_master": ("content_masters",),
    "wallet": ("wallet_accounts", "wallet_transactions"),
    "token_ledger": ("token_ledger_entries",),
    "ubrain_tenant_memory": ("ubrain_tenant_memory",),
}


@dataclass
class RLSPolicy:
    """单条 PG RLS 策略的生成规格。"""

    table: str
    policy_name: str
    tenant_id_column: str = "tenant_id"
    # 操作：SELECT / INSERT / UPDATE / DELETE / ALL
    operation: str = "ALL"
    # 角色：默认 app_user（业务用户），可选 service_role
    role: str = "app_user"
    # USING 表达式
    using_expr: str = "(tenant_id = current_setting('app.current_tenant_id')::uuid)"
    # WITH CHECK 表达式（INSERT/UPDATE 时用）
    with_check_expr: str = "(tenant_id = current_setting('app.current_tenant_id')::uuid)"
    # 额外注释
    description: str = ""


# 6 张表的策略模板（按表名索引）
# 注意：token_ledger 是全局账本，理论上不按 tenant 隔离；按 §8 仅 service_role 可读写
# 实际项目 RLS 政策可调，本轮先按统一模板出
DEFAULT_POLICIES: dict[str, list[RLSPolicy]] = {
    "leads": [
        RLSPolicy(
            table="prospect_leads",  # G.2: 物理表名（逻辑名 leads 真库不存在）
            policy_name="leads_tenant_isolation",
            description="leads 行级隔离：app_user 只能看本租户",
        ),
    ],
    "email_outreach": [
        RLSPolicy(
            table="email_outreachs",  # G.2: 物理表名（逻辑名真库不存在）
            policy_name="email_outreach_tenant_isolation",
        ),
    ],
    "content_master": [
        RLSPolicy(
            table="content_masters",  # G.2: 物理表名（逻辑名真库不存在）
            policy_name="content_master_tenant_isolation",
        ),
    ],
    "wallet": [
        RLSPolicy(
            # G.2（2026-09-11）：wallet 两张物理表无 tenant_id 列（仅 user_id varchar），
            # 租户模板策略无法套用（USING 引用不存在的列会 CREATE POLICY 失败）；
            # 改 user 维度试点条目（089_wallet_user_rls 为准，本条目只为生成器补全，
            # 策略名带 pilot 后缀，与 089 的同语义策略不撞名）。
            table="wallet_accounts",
            policy_name="wallet_accounts_pilot_user_isolation",
            role="app_user",
            using_expr="(user_id = current_setting('app.current_user_id'))",
            with_check_expr="(user_id = current_setting('app.current_user_id'))",
            description="wallet_accounts user 维度隔离（试点条目；089 为准）",
        ),
    ],
    "token_ledger": [
        # token_ledger 走 service_role 旁路 + 写时强制 tenant_id 校验
        RLSPolicy(
            table="token_ledger_entries",  # G.2: 物理表名（逻辑名真库不存在）
            policy_name="token_ledger_service_only",
            role="service_role",
            using_expr="(true)",  # service_role 看全表
            with_check_expr="(tenant_id = current_setting('app.current_tenant_id')::uuid)",
            description="token_ledger：app_user 完全禁（service_role 旁路）",
        ),
        RLSPolicy(
            table="token_ledger_entries",  # G.2: 物理表名（逻辑名真库不存在）
            policy_name="token_ledger_tenant_insert",
            role="app_user",
            operation="INSERT",
            using_expr="(false)",  # 永不读
            with_check_expr="(tenant_id = current_setting('app.current_tenant_id')::uuid)",
            description="token_ledger：app_user 仅 INSERT（含 tenant_id 校验）",
        ),
    ],
    "ubrain_tenant_memory": [
        RLSPolicy(
            table="ubrain_tenant_memory",
            policy_name="ubrain_tenant_memory_tenant_isolation",
        ),
    ],
}


# wallet 两表的用户维度隔离策略（088 跳过项，089 补齐；总纲 §8）。
# 注意：wallet_accounts/wallet_transactions 的 user_id 列是 varchar，
# 策略表达式不做 ::uuid cast——类型转换要跟列型走（088 实战教训）。
# app_user 只能读写本人账户/流水；service_role 充值与对账走全量旁路。
WALLET_USER_POLICIES: dict[str, list[RLSPolicy]] = {
    "wallet_accounts": [
        RLSPolicy(
            table="wallet_accounts",
            policy_name="wallet_accounts_user_isolation",
            role="app_user",
            using_expr="(user_id = current_setting('app.current_user_id'))",
            with_check_expr="(user_id = current_setting('app.current_user_id'))",
            description="wallet_accounts 行级隔离：app_user 只能读写本人账户",
        ),
        RLSPolicy(
            table="wallet_accounts",
            policy_name="wallet_accounts_service_bypass",
            role="service_role",
            using_expr="(true)",
            with_check_expr="(true)",
            description="wallet_accounts：service_role 充值/对账全量旁路",
        ),
    ],
    "wallet_transactions": [
        RLSPolicy(
            table="wallet_transactions",
            policy_name="wallet_transactions_user_isolation",
            role="app_user",
            using_expr="(user_id = current_setting('app.current_user_id'))",
            with_check_expr="(user_id = current_setting('app.current_user_id'))",
            description="wallet_transactions 行级隔离：app_user 只能查本人流水",
        ),
        RLSPolicy(
            table="wallet_transactions",
            policy_name="wallet_transactions_service_bypass",
            role="service_role",
            using_expr="(true)",
            with_check_expr="(true)",
            description="wallet_transactions：service_role 对账全量旁路",
        ),
    ],
}


def generate_enable_rls_sql(table: str) -> list[str]:
    """生成启用 RLS + 强制 RLS 的 SQL。

    返回 SQL 列表：
    1. ALTER TABLE ... ENABLE ROW LEVEL SECURITY
    2. ALTER TABLE ... FORCE ROW LEVEL SECURITY（确保 owner 也受 RLS 约束）
    """
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;",
    ]


def generate_disable_rls_sql(table: str) -> list[str]:
    """生成禁用 RLS 的 SQL（回滚用）。"""
    return [
        f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;",
        f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;",
    ]


def generate_policy_sql(policy: RLSPolicy) -> str:
    """生成单条策略的 CREATE POLICY SQL。

    PG 规则：INSERT 策略只允许 WITH CHECK（无 USING 子句）
    （2026-09-03 真 PG 实测修正，否则 SyntaxError）。
    """
    head = (
        f"CREATE POLICY {policy.policy_name} ON {policy.table}\n"
        f"  FOR {policy.operation}\n"
        f"  TO {policy.role}\n"
    )
    if policy.operation.upper() == "INSERT":
        return head + f"  WITH CHECK ({policy.with_check_expr});"
    return (
        head
        + f"  USING ({policy.using_expr})\n"
        f"  WITH CHECK ({policy.with_check_expr});"
    )


def generate_drop_policy_sql(policy: RLSPolicy) -> str:
    """生成单条策略的 DROP POLICY SQL（回滚用）。"""
    return f"DROP POLICY IF EXISTS {policy.policy_name} ON {policy.table};"


def physical_table_names(logical: str) -> tuple[str, ...]:
    """逻辑名 → 物理表名（G.2：生成 SQL 一律走物理名，逻辑名真库不存在）。"""
    return RLS_PILOT_TABLE_MAPPING.get(logical, (logical,))


def filter_existing_tables(connection) -> set[str]:
    """返回试点范围内在目标库中真实存在的物理表名集合。

    配合 `generate_all_pilot_sql(existing=...)` 使用：绿色链/新库缺表时
    不生成指向不存在表的 SQL（G.2 根因：逻辑名生成器在真 PG 上必崩）。"""
    from sqlalchemy import inspect

    inspector = inspect(connection)
    return {
        table
        for logical in RLS_PILOT_TABLES
        for table in physical_table_names(logical)
        if inspector.has_table(table)
    }


def generate_all_pilot_sql(
    *,
    enable: bool = True,
    existing: Optional[Iterable[str]] = None,
) -> list[str]:
    """生成 RLS 试点的全部 SQL（启用或禁用）。

    G.2（2026-09-11）：改按**物理表名**（映射）出 SQL——逻辑名
    leads/email_outreach/content_master/wallet/token_ledger 真库均不存在；
    并同出一批 WALLET_USER_POLICIES user 维度策略（按 (table, name, role, op) 去重）。

    Args:
        enable: True=启用 RLS（含 enable + 策略），False=禁用（drop + disable）
        existing: 指定时只为集合内的物理表出 SQL（传 `filter_existing_tables(conn)`）
    """

    def _keep(table: str) -> bool:
        return existing is None or table in set(existing)

    # 逻辑组 → 物理表 + 该表策略（DEFAULT + WALLET_USER_POLICIES 补全）
    planned: list[tuple[str, list[RLSPolicy]]] = []
    for logical in RLS_PILOT_TABLES:
        for table in physical_table_names(logical):
            if not _keep(table):
                continue
            policies = [p for p in DEFAULT_POLICIES.get(logical, []) if p.table == table]
            policies += list(WALLET_USER_POLICIES.get(table, []))
            planned.append((table, policies))

    # 策略去重：同名同角色同操作的策略只出一次（DEFAULT 与 WALLET_USER_POLICIES 可能同表）
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[tuple[str, list[RLSPolicy]]] = []
    for table, policies in planned:
        kept: list[RLSPolicy] = []
        for p in policies:
            key = (p.table, p.policy_name, p.role, p.operation)
            if key in seen:
                continue
            seen.add(key)
            kept.append(p)
        deduped.append((table, kept))

    sqls: list[str] = []
    if enable:
        for table, policies in deduped:
            sqls.extend(generate_enable_rls_sql(table))
            for policy in policies:
                sqls.append(generate_policy_sql(policy))
    else:
        # 逆序：先 drop 策略，再 disable
        for table, policies in reversed(deduped):
            for policy in reversed(policies):
                sqls.append(generate_drop_policy_sql(policy))
            sqls.extend(generate_disable_rls_sql(table))
    return sqls


def verify_rls_applied(table: str, inspector_dialect: str = "postgresql") -> dict[str, bool]:
    """校验某张表是否已应用 RLS（基于 SQLAlchemy Inspector 反射）。

    Args:
        table: 表名
        inspector_dialect: SQL 方言（仅 PG 支持 RLS 校验）

    Returns:
        dict 含：enabled, forced, policies_count
    """
    return {
        "enabled": False,      # 由 SQLAlchemy 反射填充（shim 路径返回 False）
        "forced": False,
        "policies_count": 0,
        "dialect_supported": inspector_dialect == "postgresql",
    }


# 导出常量
__all__ = [
    "RLS_PILOT_TABLES",
    "RLS_PILOT_TABLE_MAPPING",
    "RLSPolicy",
    "DEFAULT_POLICIES",
    "WALLET_USER_POLICIES",
    "generate_enable_rls_sql",
    "generate_disable_rls_sql",
    "generate_policy_sql",
    "generate_drop_policy_sql",
    "generate_all_pilot_sql",
    "physical_table_names",
    "filter_existing_tables",
    "verify_rls_applied",
]
