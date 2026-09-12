"""询盘来源渠道 T3

Revision ID: 027_inquiry_source_channel
Revises: 026_ubrain_commercial_os
"""

import sqlalchemy as sa
from alembic import op

revision = "027_inquiry_source_channel"
down_revision = "026_ubrain_commercial_os"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "inquiries" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("inquiries")}
    if "source_channel" not in cols:
        op.add_column(
            "inquiries",
            sa.Column("source_channel", sa.String(length=50), nullable=True),
        )
    # 2026-09-05 P0-B：index 移出 add 分支——022 建表可能已带列（幂等路径也要补 index）
    if "ix_inquiries_source_channel" not in [
        i["name"] for i in insp.get_indexes("inquiries")
    ]:
        op.create_index(
            "ix_inquiries_source_channel",
            "inquiries",
            ["source_channel"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "inquiries" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("inquiries")}
    if "source_channel" in cols:
        op.drop_index("ix_inquiries_source_channel", table_name="inquiries")
        op.drop_column("inquiries", "source_channel")
