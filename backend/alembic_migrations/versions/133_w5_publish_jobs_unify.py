# -*- coding: utf-8 -*-
"""publish_jobs 统一模型 + 凭据收口（模块 5 · M4 / M5 / 裁-8 / R9）

单一迁移，严禁拆分（避免多 head）。依据 `docs/模块5-publish_jobs收口契约-2026-09-27.md` §6.3。

- ① publish_tasks 加 4 列（content_asset_id / idempotency_key / external_id / error_code），全部可空。
- ② content_asset_id 回填历史行（自 content_master_id，不覆盖已有值）。
- ③ idempotency_key 部分唯一索引（仅非空生效）。
- ④ platform_accounts 加 credential_ref（M5 接 Vault 用；R9 并入本迁移）。
- ⑤ platform_accounts drop 漂移两列 credentials / last_used_at（裁-8 / R5）。

R5 可逆前置（已实查，2026-09-28）：`platform_accounts.credentials` 与 `last_used_at`
在 backend/app 业务代码 0 消费者（命中均为 Vault Credential 模型 / EEAT author / HTTP auth /
B2B 平台本地 dict，与 platform_accounts 无关），downgrade 可重建两列，属「可恢复」非单向销毁。

down_revision = "132_w5_content_asset_meta"（模块 4 head，DB alembic_version 实查确认）。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "133_w5_publish_jobs_unify"
down_revision = "132_w5_content_asset_meta"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ① publish_tasks 加 4 列（全部可空 + IF NOT EXISTS，幂等）
    op.execute(text("ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS content_asset_id UUID;"))
    op.execute(text("ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);"))
    op.execute(text("ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS external_id VARCHAR(200);"))
    op.execute(text("ALTER TABLE publish_tasks ADD COLUMN IF NOT EXISTS error_code VARCHAR(64);"))

    # ② content_asset_id 回填历史行（自 content_master_id；不覆盖已有值）
    op.execute(text(
        "UPDATE publish_tasks "
        "SET content_asset_id = content_master_id "
        "WHERE content_asset_id IS NULL AND content_master_id IS NOT NULL;"
    ))

    # ③ idempotency_key 部分唯一索引（仅非空生效）
    op.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_tasks_idempotency_key "
        "ON publish_tasks (idempotency_key) WHERE idempotency_key IS NOT NULL;"
    ))

    # ④ platform_accounts 加 credential_ref（M5 接 Vault 用；R9 并入本迁移）
    op.execute(text("ALTER TABLE platform_accounts ADD COLUMN IF NOT EXISTS credential_ref VARCHAR(200) NULL;"))

    # ⑤ platform_accounts drop 漂移两列（裁-8 / R5；两列现均 0 行非空 + 业务 0 消费者）
    op.execute(text("ALTER TABLE platform_accounts DROP COLUMN IF EXISTS credentials;"))
    op.execute(text("ALTER TABLE platform_accounts DROP COLUMN IF EXISTS last_used_at;"))


def downgrade() -> None:
    # ⑤⁻ 重建被 drop 的两列（按 DB 现状类型：json / timestamptz，均可空）
    op.execute(text("ALTER TABLE platform_accounts ADD COLUMN IF NOT EXISTS credentials JSON;"))
    op.execute(text("ALTER TABLE platform_accounts ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP WITH TIME ZONE;"))

    # ④⁻ 移除 credential_ref
    op.execute(text("ALTER TABLE platform_accounts DROP COLUMN IF EXISTS credential_ref;"))

    # ③⁻ 去部分唯一索引
    op.execute(text("DROP INDEX IF EXISTS uq_publish_tasks_idempotency_key;"))

    # ①⁻ 去 4 列（②⁻ 回填随列 DROP 消失，原始 content_master_id 不动 → 无损、可重放）
    op.execute(text("ALTER TABLE publish_tasks DROP COLUMN IF EXISTS error_code;"))
    op.execute(text("ALTER TABLE publish_tasks DROP COLUMN IF EXISTS external_id;"))
    op.execute(text("ALTER TABLE publish_tasks DROP COLUMN IF EXISTS idempotency_key;"))
    op.execute(text("ALTER TABLE publish_tasks DROP COLUMN IF EXISTS content_asset_id;"))
