# -*- coding: utf-8 -*-
"""134 — W5 轨7 API 市场三表（模块13 / T13）

依据 `docs/模块13-轨7API市场收口契约-2026-09-28.md` §2：
- api_products：产品生命周期面（draft/review/published/suspended/deprecated）；
- api_keys：key_hash 唯一（明文只存 sha256，绝不落库）；
- api_subscriptions：(consumer_tenant_id, api_product_id) 唯一，FK ON DELETE CASCADE。

单迁移不拆分（避免多 head）。down_revision = "133_w5_publish_jobs_unify"
（模块5 head，DB alembic_version 实查确认）。幂等建表（IF NOT EXISTS 语义由
_table_names 守卫实现，风格同 131）。
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "134_w5_api_marketplace"
down_revision: Union[str, None] = "133_w5_publish_jobs_unify"
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

    tables = _table_names()

    if "api_products" not in tables:
        op.create_table(
            "api_products",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("owner_tenant_id", UUID_TYPE, nullable=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("version", sa.String(length=20), nullable=False, server_default="v1"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("pricing_rule_id", sa.String(length=60), nullable=True),
            sa.Column("scope", sa.String(length=200), nullable=False, server_default=""),
            sa.Column("rate_limit_per_day", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("name", "version", name="uq_api_products_name_version"),
        )
        op.create_index("ix_api_products_owner", "api_products", ["owner_tenant_id"])
        op.create_index("ix_api_products_status", "api_products", ["status"])

    if "api_keys" not in tables:
        op.create_table(
            "api_keys",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("tenant_id", UUID_TYPE, nullable=False),
            sa.Column("key_hash", sa.String(length=64), nullable=False),
            sa.Column("key_prefix", sa.String(length=16), nullable=False),
            sa.Column("label", sa.String(length=120), nullable=True),
            sa.Column("scopes", sa.String(length=500), nullable=False, server_default=""),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
        )
        op.create_index("ix_api_keys_tenant", "api_keys", ["tenant_id"])

    if "api_subscriptions" not in tables:
        op.create_table(
            "api_subscriptions",
            sa.Column("id", UUID_TYPE, primary_key=True),
            sa.Column("consumer_tenant_id", UUID_TYPE, nullable=False),
            sa.Column(
                "api_product_id",
                UUID_TYPE,
                sa.ForeignKey("api_products.id", ondelete="CASCADE", name="fk_api_subscriptions_product"),
                nullable=False,
            ),
            sa.Column("plan", sa.String(length=30), nullable=False, server_default="free"),
            sa.Column("quota_per_day", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "consumer_tenant_id", "api_product_id", name="uq_api_subscriptions_tenant_product"
            ),
        )
        op.create_index("ix_api_subscriptions_consumer", "api_subscriptions", ["consumer_tenant_id"])
        op.create_index("ix_api_subscriptions_status", "api_subscriptions", ["status"])


def downgrade() -> None:
    tables = _table_names()
    if "api_subscriptions" in tables:
        for ix in ("ix_api_subscriptions_status", "ix_api_subscriptions_consumer"):
            if ix in _index_names("api_subscriptions"):
                op.drop_index(ix, table_name="api_subscriptions")
        op.drop_table("api_subscriptions")
    if "api_keys" in tables:
        if "ix_api_keys_tenant" in _index_names("api_keys"):
            op.drop_index("ix_api_keys_tenant", table_name="api_keys")
        op.drop_table("api_keys")
    if "api_products" in tables:
        for ix in ("ix_api_products_status", "ix_api_products_owner"):
            if ix in _index_names("api_products"):
                op.drop_index(ix, table_name="api_products")
        op.drop_table("api_products")
