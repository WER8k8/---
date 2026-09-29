# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""RLS 第一批扩展生成器测试（修正设计稿 模块16）。

锁定语义：
- 第一批 11 表每表恰有 隔离 + 旁路 两条策略；
- generate_all_pilot_sql 输出含第一批的全部 ALTER/CREATE/DROP；
- 元数据层前提：凡在 ORM 元数据中的第一批表必含 tenant_id 列
  （PG 侧列型差异——inquiries 为 VARCHAR——由迁移 125 分组处理，见 088 教训）。
"""
from __future__ import annotations

import app.models  # noqa: F401 — 注册全部模型到 metadata
from app.core.database import Base
from app.db.rls_policies import (
    FIRST_BATCH_POLICIES,
    RLS_FIRST_BATCH_TABLES,
    generate_all_pilot_sql,
)


class TestFirstBatchPolicies:
    def test_eleven_tables_with_pair_policies(self):
        assert len(RLS_FIRST_BATCH_TABLES) == 11
        for table in RLS_FIRST_BATCH_TABLES:
            policies = FIRST_BATCH_POLICIES[table]
            names = {p.policy_name for p in policies}
            assert f"{table}_tenant_isolation" in names, table
            assert f"{table}_service_bypass" in names, table
            isolation = next(p for p in policies if p.policy_name.endswith("_tenant_isolation"))
            assert isolation.role == "app_user"
            assert isolation.operation == "ALL"
            bypass = next(p for p in policies if p.policy_name.endswith("_service_bypass"))
            assert bypass.role == "service_role"

    def test_metadata_tenant_id_precondition(self):
        """凡在 ORM 元数据中的第一批表必须含 tenant_id 列（模型层防线）。"""
        for table in RLS_FIRST_BATCH_TABLES:
            model_table = Base.metadata.tables.get(table)
            if model_table is None:
                continue  # 运行时表（如 inquiries 归因列由 healer 补齐）
            assert "tenant_id" in model_table.columns, f"{table} 缺 tenant_id 列"

    def test_generate_sql_covers_first_batch(self):
        enable_sql = "\n".join(generate_all_pilot_sql(enable=True))
        for table in RLS_FIRST_BATCH_TABLES:
            assert f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in enable_sql, table
            assert f"CREATE POLICY {table}_tenant_isolation ON {table}" in enable_sql, table
            assert f"CREATE POLICY {table}_service_bypass ON {table}" in enable_sql, table

        disable_sql = "\n".join(generate_all_pilot_sql(enable=False))
        for table in RLS_FIRST_BATCH_TABLES:
            assert f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}" in disable_sql, table
            assert f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY" in disable_sql, table
