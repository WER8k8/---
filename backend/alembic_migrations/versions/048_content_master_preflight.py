"""content_masters 发布前人审清单持久化

Revision ID: 048_content_master_preflight
Revises: 047_egress_suppliers

2026-09-05 P0-B 绿色链修复：content_masters 在全迁移链上原本无人建表
（活库靠 create_all 掩盖，052 对其 add deleted_at 时绿色链 UndefinedTable 崩）。
本迁移升级为建表点：表不存在时按模型 app/models/content_master.py 转写全表
（uuid_col 方言对齐 UUID_TYPE），已存在则只做 preflight 三列幂等补齐。
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "048_content_master_preflight"
down_revision = "047_egress_suppliers"
branch_labels = None
depends_on = None


def _uuid_col():
    """canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


def _col_names(table: str) -> set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    cols = _col_names("content_masters")
    if not cols:
        # 建表点：content_masters 全表（对齐 ContentMaster 模型）
        op.create_table(
            "content_masters",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("media_urls", sa.JSON(), nullable=True),
            sa.Column("content_type", sa.String(30), server_default="article", nullable=True),
            sa.Column("tenant_canonical_url", sa.String(1000), nullable=True),
            sa.Column("status", sa.String(20), server_default="draft", nullable=True),
            sa.Column("hub_slug", sa.String(200), nullable=True),
            sa.Column("hub_summary", sa.Text(), nullable=True),
            sa.Column("show_on_hub", sa.Boolean(), server_default=sa.true(), nullable=True),
            sa.Column("hub_published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", _uuid_col(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("preflight_checklist_json", sa.Text(), nullable=True),
            sa.Column("preflight_approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("preflight_approved_by", _uuid_col(), sa.ForeignKey("users.id"), nullable=True),
        )
        op.create_index("ix_content_masters_tenant_id", "content_masters", ["tenant_id"])
        return
    with op.batch_alter_table("content_masters") as batch:
        if "preflight_checklist_json" not in cols:
            batch.add_column(sa.Column("preflight_checklist_json", sa.Text(), nullable=True))
        if "preflight_approved_at" not in cols:
            batch.add_column(
                sa.Column("preflight_approved_at", sa.DateTime(timezone=True), nullable=True)
            )
        if "preflight_approved_by" not in cols:
            batch.add_column(
                sa.Column("preflight_approved_by", _uuid_col(), nullable=True)
            )


def downgrade() -> None:
    # 表由本迁移兜底创建时也不 drop：可能已承载业务数据，且后续迁移
    # （052 等）语义上以该表为存在前提。仅回退 preflight 列。
    cols = _col_names("content_masters")
    if not cols:
        return
    with op.batch_alter_table("content_masters") as batch:
        if "preflight_approved_by" in cols:
            batch.drop_column("preflight_approved_by")
        if "preflight_approved_at" in cols:
            batch.drop_column("preflight_approved_at")
        if "preflight_checklist_json" in cols:
            batch.drop_column("preflight_checklist_json")
