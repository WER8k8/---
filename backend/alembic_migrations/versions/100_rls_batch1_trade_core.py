"""Batch 1 交易核心表 RLS 租户隔离 (改造6)。

应用表：products, inquiries, orders, payment_orders, rfqs
"""
from __future__ import annotations

import logging
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "100_rls_batch1_trade_core"
down_revision: Union[str, None] = "089_wallet_user_rls"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = logging.getLogger("alembic.env.rls_batch1_trade_core")

BATCH1_TABLES = ("products", "inquiries", "orders", "payment_orders", "rfqs")

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        logger.warning("RLS skipped: dialect=%s (only PostgreSQL supported)", bind.dialect.name)
        return

    # 为避免循环依赖，我们直接生成 RLS SQL
    # 策略规格：
    # 1. 业务用户 (app_user) 必须带 tenant_id 进行查询/修改
    # 2. 只有 tenant_id = app.current_tenant_id 才能操作
    # 3. 超级服务角色 (service_role) 旁路，拥有全部权限

    # 2026-09-05 P0-B：角色幂等预建（同 088）+ 缺表跳过
    # （rfqs 等模型表绿色链可能未建出，活库靠 create_all）
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

    for table in BATCH1_TABLES:
        if table not in existing_tables:
            logger.warning("RLS skipped (table absent): %s", table)
            continue
        # 2026-09-05 P0-B：本迁移 << 102（tenant 统一加列）。products/orders 等表
        # 在绿色链此时尚无 tenant_id 列，策略 USING(tenant_id=...) 必崩
        # UndefinedColumn。无列跳过（RLS 语义本就依赖该列），102 后如需补 RLS 另行迁移。
        cols = {c["name"] for c in sa.inspect(bind).get_columns(table)}
        if "tenant_id" not in cols:
            logger.warning("RLS skipped (no tenant_id column yet): %s", table)
            continue
        # 1. Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        
        # 2. Create app_user policy
        # P0-B：tenant_id 列类型在存量库存在 varchar/uuid 分裂，
        # 统一按 text 比较兼容两种类型（current_setting 本身返回 text）
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            FOR ALL
            TO app_user
            USING (tenant_id::text = current_setting('app.current_tenant_id'))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id'));
        """)
        
        # 3. Create service_role bypass policy
        op.execute(f"""
            CREATE POLICY {table}_service_bypass ON {table}
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
        """)
        logger.info("Applied RLS to %s", table)

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    existing_tables = set(sa.inspect(bind).get_table_names())
    for table in reversed(BATCH1_TABLES):
        if table not in existing_tables:
            continue
        op.execute(f"DROP POLICY IF EXISTS {table}_service_bypass ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        logger.info("Removed RLS from %s", table)
