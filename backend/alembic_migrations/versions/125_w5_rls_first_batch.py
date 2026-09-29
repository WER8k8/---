# -*- coding: utf-8 -*-
"""125 — W5 RLS 第一批扩展：11 张租户表启用行级隔离（修正设计稿 模块16 / Gate G1）

表清单 = 真库实测含 tenant_id 列的 11 张租户表；每表两条策略：
- {table}_tenant_isolation：app_user，ALL，tenant_id = current_setting
- {table}_service_bypass：service_role 全量旁路（后台任务/迁移/统计须审计）

**不加 FORCE**：表属主（应用连接）旁路，运行时零影响；FORCE 待租户注入全链路
就绪后另评（设计稿 16.2）。幂等：DO 块内逐策略查 pg_policies。
排除（无 tenant_id 列）：order_items / inbox_events / content_pages / shipping_timeline。
配套生成器（策略清单/SQL 生成）：app/db/rls_policies.py 的
RLS_FIRST_BATCH_TABLES + FIRST_BATCH_POLICIES。

依赖：down_revision = 124_w5_billing_reservations
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "125_w5_rls_first_batch"
down_revision: Union[str, None] = "124_w5_billing_reservations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='inquiries' AND policyname='inquiries_tenant_isolation') THEN
    ALTER TABLE inquiries ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY inquiries_tenant_isolation ON inquiries FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id''))';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='inquiries' AND policyname='inquiries_service_bypass') THEN
    EXECUTE 'CREATE POLICY inquiries_service_bypass ON inquiries FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='orders' AND policyname='orders_tenant_isolation') THEN
    ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY orders_tenant_isolation ON orders FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='orders' AND policyname='orders_service_bypass') THEN
    EXECUTE 'CREATE POLICY orders_service_bypass ON orders FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='platform_accounts' AND policyname='platform_accounts_tenant_isolation') THEN
    ALTER TABLE platform_accounts ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY platform_accounts_tenant_isolation ON platform_accounts FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='platform_accounts' AND policyname='platform_accounts_service_bypass') THEN
    EXECUTE 'CREATE POLICY platform_accounts_service_bypass ON platform_accounts FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='finance_ledger_entries' AND policyname='finance_ledger_entries_tenant_isolation') THEN
    ALTER TABLE finance_ledger_entries ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY finance_ledger_entries_tenant_isolation ON finance_ledger_entries FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='finance_ledger_entries' AND policyname='finance_ledger_entries_service_bypass') THEN
    EXECUTE 'CREATE POLICY finance_ledger_entries_service_bypass ON finance_ledger_entries FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='meter_events' AND policyname='meter_events_tenant_isolation') THEN
    ALTER TABLE meter_events ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY meter_events_tenant_isolation ON meter_events FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='meter_events' AND policyname='meter_events_service_bypass') THEN
    EXECUTE 'CREATE POLICY meter_events_service_bypass ON meter_events FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='billing_reservations' AND policyname='billing_reservations_tenant_isolation') THEN
    ALTER TABLE billing_reservations ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY billing_reservations_tenant_isolation ON billing_reservations FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='billing_reservations' AND policyname='billing_reservations_service_bypass') THEN
    EXECUTE 'CREATE POLICY billing_reservations_service_bypass ON billing_reservations FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='outbox_events' AND policyname='outbox_events_tenant_isolation') THEN
    ALTER TABLE outbox_events ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY outbox_events_tenant_isolation ON outbox_events FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='outbox_events' AND policyname='outbox_events_service_bypass') THEN
    EXECUTE 'CREATE POLICY outbox_events_service_bypass ON outbox_events FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='dead_letter_events' AND policyname='dead_letter_events_tenant_isolation') THEN
    ALTER TABLE dead_letter_events ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY dead_letter_events_tenant_isolation ON dead_letter_events FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='dead_letter_events' AND policyname='dead_letter_events_service_bypass') THEN
    EXECUTE 'CREATE POLICY dead_letter_events_service_bypass ON dead_letter_events FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='tenant_domains' AND policyname='tenant_domains_tenant_isolation') THEN
    ALTER TABLE tenant_domains ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY tenant_domains_tenant_isolation ON tenant_domains FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='tenant_domains' AND policyname='tenant_domains_service_bypass') THEN
    EXECUTE 'CREATE POLICY tenant_domains_service_bypass ON tenant_domains FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='user_tenants' AND policyname='user_tenants_tenant_isolation') THEN
    ALTER TABLE user_tenants ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY user_tenants_tenant_isolation ON user_tenants FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='user_tenants' AND policyname='user_tenants_service_bypass') THEN
    EXECUTE 'CREATE POLICY user_tenants_service_bypass ON user_tenants FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='tenant_subscriptions' AND policyname='tenant_subscriptions_tenant_isolation') THEN
    ALTER TABLE tenant_subscriptions ENABLE ROW LEVEL SECURITY;
    EXECUTE 'CREATE POLICY tenant_subscriptions_tenant_isolation ON tenant_subscriptions FOR ALL TO app_user USING (tenant_id = current_setting(''app.current_tenant_id'')::uuid) WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'')::uuid)';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='tenant_subscriptions' AND policyname='tenant_subscriptions_service_bypass') THEN
    EXECUTE 'CREATE POLICY tenant_subscriptions_service_bypass ON tenant_subscriptions FOR ALL TO service_role USING (true) WITH CHECK (true)';
  END IF;
END $$;
""")


def downgrade() -> None:
    op.execute("""
DO $$
BEGIN
  DROP POLICY IF EXISTS tenant_subscriptions_service_bypass ON tenant_subscriptions;
  DROP POLICY IF EXISTS tenant_subscriptions_tenant_isolation ON tenant_subscriptions;
  ALTER TABLE tenant_subscriptions NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE tenant_subscriptions DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS user_tenants_service_bypass ON user_tenants;
  DROP POLICY IF EXISTS user_tenants_tenant_isolation ON user_tenants;
  ALTER TABLE user_tenants NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE user_tenants DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS tenant_domains_service_bypass ON tenant_domains;
  DROP POLICY IF EXISTS tenant_domains_tenant_isolation ON tenant_domains;
  ALTER TABLE tenant_domains NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE tenant_domains DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS dead_letter_events_service_bypass ON dead_letter_events;
  DROP POLICY IF EXISTS dead_letter_events_tenant_isolation ON dead_letter_events;
  ALTER TABLE dead_letter_events NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE dead_letter_events DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS outbox_events_service_bypass ON outbox_events;
  DROP POLICY IF EXISTS outbox_events_tenant_isolation ON outbox_events;
  ALTER TABLE outbox_events NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE outbox_events DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS billing_reservations_service_bypass ON billing_reservations;
  DROP POLICY IF EXISTS billing_reservations_tenant_isolation ON billing_reservations;
  ALTER TABLE billing_reservations NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE billing_reservations DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS meter_events_service_bypass ON meter_events;
  DROP POLICY IF EXISTS meter_events_tenant_isolation ON meter_events;
  ALTER TABLE meter_events NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE meter_events DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS finance_ledger_entries_service_bypass ON finance_ledger_entries;
  DROP POLICY IF EXISTS finance_ledger_entries_tenant_isolation ON finance_ledger_entries;
  ALTER TABLE finance_ledger_entries NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE finance_ledger_entries DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS platform_accounts_service_bypass ON platform_accounts;
  DROP POLICY IF EXISTS platform_accounts_tenant_isolation ON platform_accounts;
  ALTER TABLE platform_accounts NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE platform_accounts DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS orders_service_bypass ON orders;
  DROP POLICY IF EXISTS orders_tenant_isolation ON orders;
  ALTER TABLE orders NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE orders DISABLE ROW LEVEL SECURITY;
  DROP POLICY IF EXISTS inquiries_service_bypass ON inquiries;
  DROP POLICY IF EXISTS inquiries_tenant_isolation ON inquiries;
  ALTER TABLE inquiries NO FORCE ROW LEVEL SECURITY;
  ALTER TABLE inquiries DISABLE ROW LEVEL SECURITY;
END $$;
""")
