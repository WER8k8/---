"""add purchased_token_bonus column to tenants table

Revision ID: 081
Revises: 069_add_evolution_deerflow
Create Date: 2026-08-30

BUG-01 修复：为 tenants 表添加 purchased_token_bonus 字段，
用于记录已购 Token 额度（充值/推荐奖励），独立于套餐基础额度。
修复 Token 充值被 max(0,...) 截断吞额度的资损问题。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '081'
down_revision: Union[str, None] = '069_add_evolution_deerflow'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查列是否已存在（SQLite 和 PostgreSQL 兼容）
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        # PostgreSQL: 使用 DO 块检查并添加列
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tenants' AND column_name = 'purchased_token_bonus'
                ) THEN
                    ALTER TABLE tenants ADD COLUMN purchased_token_bonus INTEGER NOT NULL DEFAULT 0;
                END IF;
            END $$;
        """)
    else:
        # SQLite: 需要重建表
        # 先检查是否已存在
        result = conn.execute(
            sa.text("PRAGMA table_info(tenants)")
        )
        columns = [row[1] for row in result.fetchall()]

        if "purchased_token_bonus" not in columns:
            # SQLite 不支持 ALTER TABLE ADD COLUMN IF NOT EXISTS
            # 需要重建表
            op.execute("""
                CREATE TABLE tenants_new (
                    id VARCHAR(36) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    contact_name VARCHAR(100),
                    contact_email VARCHAR(200),
                    contact_phone VARCHAR(50),
                    domain VARCHAR(200) NOT NULL,
                    custom_domains TEXT DEFAULT '',
                    plan_id VARCHAR(36) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'trial',
                    trial_ends_at TIMESTAMP WITH TIME ZONE,
                    subscribed_at TIMESTAMP WITH TIME ZONE,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    ai_quota_used INTEGER NOT NULL DEFAULT 0,
                    purchased_token_bonus INTEGER NOT NULL DEFAULT 0,
                    storage_used INTEGER NOT NULL DEFAULT 0,
                    settings TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    PRIMARY KEY (id),
                    FOREIGN KEY(plan_id) REFERENCES tenant_plans (id)
                )
            """)
            # 复制数据
            op.execute("""
                INSERT INTO tenants_new
                SELECT id, name, contact_name, contact_email, contact_phone, domain,
                       custom_domains, plan_id, status, trial_ends_at, subscribed_at,
                       expires_at, ai_quota_used, 0, storage_used, settings, is_active,
                       created_at, updated_at
                FROM tenants
            """)
            # 删除旧表，重命名新表
            op.execute("DROP TABLE tenants")
            op.execute("ALTER TABLE tenants_new RENAME TO tenants")
            # 重新创建索引
            op.create_index("ix_tenants_domain", "tenants", ["domain"])
            op.create_index("ix_tenants_plan_id", "tenants", ["plan_id"])
            op.create_index("ix_tenants_status", "tenants", ["status"])

    # 添加注释（仅 PostgreSQL）
    if dialect == "postgresql":
        op.execute("""
            COMMENT ON COLUMN tenants.purchased_token_bonus IS
            '已购 Token 额度（充值/推荐奖励，独立于套餐基础额度）'
        """)


def downgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS purchased_token_bonus")
    else:
        # SQLite downgrade 需要重建表
        op.execute("""
            CREATE TABLE tenants_new (
                id VARCHAR(36) NOT NULL,
                name VARCHAR(200) NOT NULL,
                contact_name VARCHAR(100),
                contact_email VARCHAR(200),
                contact_phone VARCHAR(50),
                domain VARCHAR(200) NOT NULL,
                custom_domains TEXT DEFAULT '',
                plan_id VARCHAR(36) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'trial',
                trial_ends_at TIMESTAMP WITH TIME ZONE,
                subscribed_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE,
                ai_quota_used INTEGER NOT NULL DEFAULT 0,
                storage_used INTEGER NOT NULL DEFAULT 0,
                settings TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(plan_id) REFERENCES tenant_plans (id)
            )
        """)
        op.execute("""
            INSERT INTO tenants_new
            SELECT id, name, contact_name, contact_email, contact_phone, domain,
                   custom_domains, plan_id, status, trial_ends_at, subscribed_at,
                   expires_at, ai_quota_used, storage_used, settings, is_active,
                   created_at, updated_at
            FROM tenants
        """)
        op.execute("DROP TABLE tenants")
        op.execute("ALTER TABLE tenants_new RENAME TO tenants")
        op.create_index("ix_tenants_domain", "tenants", ["domain"])
        op.create_index("ix_tenants_plan_id", "tenants", ["plan_id"])
        op.create_index("ix_tenants_status", "tenants", ["status"])
