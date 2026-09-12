"""添加软删除字段 deleted_at

Revision ID: 052_soft_delete
Revises: 051_merge_heads
Create Date: 2026-07-19

2026-09-05 P0-B：幂等化——活库 create_all 建表已含 deleted_at（SoftDeleteMixin），
绿色链 048 兜底建的 content_masters 则无（由本迁移补）。列存在性守卫双路径通吃。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "052_soft_delete"
down_revision = "051_merge_heads"
branch_labels = None
depends_on = None

TABLES = ("products", "inquiries", "content_pages", "content_masters")


def upgrade() -> None:
    insp = inspect(op.get_bind())
    existing = set(insp.get_table_names())
    for t in TABLES:
        if t not in existing:
            continue
        cols = {c["name"] for c in insp.get_columns(t)}
        if "deleted_at" in cols:
            continue
        op.add_column(t, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True))


def downgrade() -> None:
    insp = inspect(op.get_bind())
    existing = set(insp.get_table_names())
    for t in TABLES:
        if t not in existing:
            continue
        cols = {c["name"] for c in insp.get_columns(t)}
        if "deleted_at" in cols:
            op.drop_column(t, "deleted_at")
