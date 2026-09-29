# -*- coding: utf-8 -*-
"""123 — W5 租户域名状态真源表：tenant_domains（验证/SSL/主域/激活）

背景（修正设计稿 模块1 / Production Gate G2）：
- 既有绑定入口把域名存 tenant.custom_domains JSON —— 无状态机、无主域唯一性，
  且未验证域名即可公开解析（违反 G2 红线）。本表承接状态真源：
  verification_status（pending/verified/failed）· ssl_status · is_primary · is_active。
- middleware 升级为 verified+active 才解析（legacy JSON 进入只读兼容期）。
- normalized_hostname 全局唯一（domain → tenant 单一真源）。

设计：幂等建表（先 inspect），与 119/120/121/122 同风格。
依赖：down_revision = 122_w5_outbox_inbox_dlq
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "123_w5_tenant_domains"
down_revision: Union[str, None] = "122_w5_outbox_inbox_dlq"
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
    from app.core.database import UUID_TYPE

    if "tenant_domains" in _table_names():
        return

    op.create_table(
        "tenant_domains",
        sa.Column("id", UUID_TYPE, primary_key=True),
        sa.Column("tenant_id", UUID_TYPE, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("normalized_hostname", sa.String(length=255), nullable=False),
        sa.Column("domain_type", sa.String(length=30), nullable=False, server_default="custom"),
        sa.Column("verification_method", sa.String(length=20), nullable=False, server_default="dns_txt"),
        sa.Column("verification_token_hash", sa.String(length=128), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("verification_failed_reason", sa.String(length=255), nullable=True),
        sa.Column("ssl_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("canonical_redirect_to", sa.String(length=255), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_ssl_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("normalized_hostname", name="uq_tenant_domains_normalized"),
    )
    op.create_index("ix_tenant_domains_tenant", "tenant_domains", ["tenant_id"])
    op.create_index("ix_tenant_domains_verify", "tenant_domains", ["verification_status"])


def downgrade() -> None:
    if "tenant_domains" not in _table_names():
        return
    indexes = _index_names("tenant_domains")
    for ix in ("ix_tenant_domains_verify", "ix_tenant_domains_tenant"):
        if ix in indexes:
            op.drop_index(ix, table_name="tenant_domains")
    op.drop_table("tenant_domains")
