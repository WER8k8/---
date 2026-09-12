"""platform tenant origins audit

Revision ID: 040_platform_tenant_origins
Revises: 039_hermes_plugin_installs
Create Date: 2026-06-02
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "040_platform_tenant_origins"
down_revision = "039_hermes_plugin_installs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 2026-09-05 P0-B：补建 platforms 兜底表（模型 app/models/content.py Platform）。
    # 全迁移链无任何迁移创建 platforms，本表 FK(platforms.id) 在绿色 PG 链上
    # UndefinedTable；活库此前靠 create_all 掩盖。守卫式：已存在则跳过。
    insp = sa.inspect(op.get_bind())
    if "platforms" not in insp.get_table_names():
        op.create_table(
            "platforms",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("platform_type", sa.String(50), nullable=False),
            sa.Column("icon", sa.String(200), nullable=True),
            sa.Column("base_url", sa.String(500), nullable=True),
            sa.Column("region", sa.String(20), server_default="cn", nullable=True),
            sa.Column("content_type", sa.String(30), server_default="article", nullable=True),
            sa.Column("has_api", sa.Boolean(), server_default=sa.false(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_platforms_region", "platforms", ["region"])

    op.create_table(
        "platform_tenant_origins",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("platform_id", _uuid_col(), sa.ForeignKey("platforms.id"), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("tenant_name", sa.String(200), nullable=True),
        sa.Column("platform_name", sa.String(200), nullable=False),
        sa.Column("is_new_platform", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("nurture_rules", sa.JSON(), nullable=True),
        sa.Column(
            "browser_profile_id",
            _uuid_col(),
            sa.ForeignKey("browser_profiles.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_platform_tenant_origins_tenant_id",
        "platform_tenant_origins",
        ["tenant_id"],
    )
    op.create_index(
        "ix_platform_tenant_origins_platform_id",
        "platform_tenant_origins",
        ["platform_id"],
    )
    op.create_index(
        "ix_platform_tenant_origins_source",
        "platform_tenant_origins",
        ["source"],
    )
    op.create_index(
        "ix_platform_tenant_origins_created_at",
        "platform_tenant_origins",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_tenant_origins_created_at", table_name="platform_tenant_origins")
    op.drop_index("ix_platform_tenant_origins_source", table_name="platform_tenant_origins")
    op.drop_index("ix_platform_tenant_origins_platform_id", table_name="platform_tenant_origins")
    op.drop_index("ix_platform_tenant_origins_tenant_id", table_name="platform_tenant_origins")
    op.drop_table("platform_tenant_origins")
