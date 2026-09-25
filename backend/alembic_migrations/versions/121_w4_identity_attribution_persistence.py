# -*- coding: utf-8 -*-
"""121 — W4 身份与归因持久化：BuyerMaster 身份锁 + 内容归因 真源表

背景（团队任务 #5 · W4）：
- ``BuyerMasterStore``（``services/acquisition/__init__.py``）与
  ``ContentAttributionStore``（``services/acquisition/growth_ops.py``）原为**纯内存**，
  进程重启即丢，无法作为「全渠道唯一身份」与「内容 → 询盘归因」的真源。
  本迁移建立对应物理表，配套 ``services/acquisition/identity_pg.py`` 写穿持久化。

新增表：
    1. ``acquisition_buyer_masters``        身份锁主档
       - buyer_id 主键；(tenant_id, email) 唯一性由索引 + 应用层身份锁保证
       - payload JSONB 存完整 BuyerMaster（新增字段无需再迁移）
    2. ``acquisition_content_touches``      内容归因主档
       - content_id 主键；payload JSONB 存完整 ContentTouch
    3. ``acquisition_content_inquiry_links`` 内容 ↔ 询盘 关联（多对多）
       - (inquiry_id, content_id) 复合主键

设计：
- 全部操作**幂等**（先 inspect 表/索引是否存在），与 119/120 同风格，
  兼容历史 bootstrap（``identity_pg.ensure_tables`` 也会 CREATE IF NOT EXISTS）。
- downgrade 仅删本迁移新建的对象，不触碰其它表。

依赖：down_revision = 120_w1_acquisition_backpoints
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "121_w4_identity_attribution_persistence"
down_revision: Union[str, None] = "120_w1_acquisition_backpoints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _index_names(table: str) -> set[str]:
    try:
        return {i["name"] for i in sa.inspect(op.get_bind()).get_indexes(table)}
    except Exception:  # noqa: BLE001
        return set()


def upgrade() -> None:
    tables = _table_names()

    # ── 1) acquisition_buyer_masters 身份锁主档 ──────────────────────────
    if "acquisition_buyer_masters" not in tables:
        op.create_table(
            "acquisition_buyer_masters",
            sa.Column("buyer_id", sa.Text(), primary_key=True),
            sa.Column("tenant_id", sa.Text(), nullable=True),
            sa.Column("email", sa.Text(), nullable=True),
            sa.Column(
                "persona_locked", sa.Boolean(), nullable=True, server_default=sa.text("true")
            ),
            sa.Column("payload", postgresql.JSONB(), nullable=False),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
            ),
        )
    idx_buyer = _index_names("acquisition_buyer_masters")
    if "ix_acq_buyer_masters_tenant" not in idx_buyer:
        op.create_index(
            "ix_acq_buyer_masters_tenant", "acquisition_buyer_masters", ["tenant_id"]
        )
    if "ix_acq_buyer_masters_tenant_email" not in idx_buyer:
        # 函数索引（lower(email)）用原生 SQL，保证 Alembic 生成合法 DDL
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_acq_buyer_masters_tenant_email "
            "ON acquisition_buyer_masters (tenant_id, lower(email))"
        )

    # ── 2) acquisition_content_touches 内容归因主档 ──────────────────────
    if "acquisition_content_touches" not in tables:
        op.create_table(
            "acquisition_content_touches",
            sa.Column("content_id", sa.Text(), primary_key=True),
            sa.Column("tenant_id", sa.Text(), nullable=True),
            sa.Column("content_title", sa.Text(), nullable=True),
            sa.Column("content_type", sa.Text(), nullable=True),
            sa.Column("channel", sa.Text(), nullable=True),
            sa.Column("published_at", sa.Text(), nullable=True),
            sa.Column("payload", postgresql.JSONB(), nullable=False),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
            ),
        )
    idx_content = _index_names("acquisition_content_touches")
    if "ix_acq_content_touches_tenant" not in idx_content:
        op.create_index(
            "ix_acq_content_touches_tenant", "acquisition_content_touches", ["tenant_id"]
        )

    # ── 3) acquisition_content_inquiry_links 内容 ↔ 询盘 关联 ───────────
    if "acquisition_content_inquiry_links" not in tables:
        op.create_table(
            "acquisition_content_inquiry_links",
            sa.Column("inquiry_id", sa.Text(), nullable=False),
            sa.Column("content_id", sa.Text(), nullable=False),
            sa.Column("tenant_id", sa.Text(), nullable=True),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
            ),
            sa.PrimaryKeyConstraint("inquiry_id", "content_id", name="pk_acq_content_links"),
        )
    idx_links = _index_names("acquisition_content_inquiry_links")
    if "ix_acq_content_links_content" not in idx_links:
        op.create_index(
            "ix_acq_content_links_content",
            "acquisition_content_inquiry_links",
            ["content_id"],
        )


def downgrade() -> None:
    tables = _table_names()

    if "acquisition_content_inquiry_links" in tables:
        if "ix_acq_content_links_content" in _index_names(
            "acquisition_content_inquiry_links"
        ):
            op.drop_index(
                "ix_acq_content_links_content",
                table_name="acquisition_content_inquiry_links",
            )
        op.drop_table("acquisition_content_inquiry_links")

    if "acquisition_content_touches" in tables:
        if "ix_acq_content_touches_tenant" in _index_names("acquisition_content_touches"):
            op.drop_index(
                "ix_acq_content_touches_tenant", table_name="acquisition_content_touches"
            )
        op.drop_table("acquisition_content_touches")

    if "acquisition_buyer_masters" in tables:
        idx_buyer = _index_names("acquisition_buyer_masters")
        for name in ("ix_acq_buyer_masters_tenant_email", "ix_acq_buyer_masters_tenant"):
            if name in idx_buyer:
                op.drop_index(name, table_name="acquisition_buyer_masters")
        op.drop_table("acquisition_buyer_masters")
