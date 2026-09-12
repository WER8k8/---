"""inquiry assigned_to for platform lead CRM

Revision ID: 036_inquiry_assigned_to
Revises: 035_invoice_applications
Create Date: 2026-05-31

2026-09-05 P0-B 绿色链修复：恢复被注释的 add_column（幂等守卫）。
历史注释原因：活库 inquiries 由 create_all 建出（模型含 assigned_to），
add_column 会 DuplicateColumn——故只留 index。绿色链 022 建的 inquiries
（迁移版定义）无此列，直接建 index 必崩 UndefinedColumn。
幂等 add_column 同时满足两条路径；列型 String(36) 无 FK，与模型一致。
"""

from alembic import op
import sqlalchemy as sa

revision = "036_inquiry_assigned_to"
down_revision = "035_invoice_applications"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return column in [c["name"] for c in insp.get_columns(table)]


def upgrade() -> None:
    if not _has_column("inquiries", "assigned_to"):
        op.add_column(
            "inquiries",
            sa.Column("assigned_to", sa.String(36), nullable=True),
        )
    insp = sa.inspect(op.get_bind())
    if "ix_inquiries_assigned_to" not in [
        i["name"] for i in insp.get_indexes("inquiries")
    ]:
        op.create_index("ix_inquiries_assigned_to", "inquiries", ["assigned_to"])


def downgrade() -> None:
    op.drop_index("ix_inquiries_assigned_to", table_name="inquiries")
    if _has_column("inquiries", "assigned_to"):
        op.drop_column("inquiries", "assigned_to")
