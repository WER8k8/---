"""registries: skills / mcp / plugins / data source providers

Revision ID: 083
Revises: 082
Create Date: 2026-08-31

总纲 §4.6-4/§5.2.4/§8 定稿：能力注册表族持久化（替代内存 list）。
skills 字段融合：
- GoodJob manifest 规范（§5.1.2：triggers/keywords/modules/tool_refs/source_type/license）；
- Trade AI BaseSkill 契约（§5.2.2：input_schema/output_schema/config_schema）；
- 版本化与发布门禁（§1.2-4：Draft→评估→Canary→人审）。
mcp：替代 agent_hub_service 内存 list（§4.3 差距项），凭证仅存 Vault ref（087）。
data_source_providers：§5.2.4 数据源合规评审清单，裁决权归 Policy Engine。
约束：租户可空=平台级资产；租户行=租户私有/启用开关；默认最小权限。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


# revision identifiers, used by Alembic.
revision: str = '083'
down_revision: Union[str, None] = '082'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SKILL_STATUSES = ('draft', 'testing', 'active', 'disabled', 'rollback')


def _table_exists(conn, name: str) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = :n"
            ),
            {"n": name},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name = :n"
            ),
            {"n": name},
        ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------ skills
    if not _table_exists(conn, "skills"):
        op.create_table(
            "skills",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("display_name", sa.String(length=200), nullable=True),
            sa.Column("category", sa.String(length=60), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("current_version", sa.String(length=40), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            # GoodJob manifest 规范
            sa.Column("triggers_json", sa.Text(), nullable=True),
            sa.Column("keywords_json", sa.Text(), nullable=True),
            sa.Column("modules_json", sa.Text(), nullable=True),
            sa.Column("tool_refs_json", sa.Text(), nullable=True),
            sa.Column("source_type", sa.String(length=30), nullable=False, server_default="builtin"),
            sa.Column("license", sa.String(length=120), nullable=True),
            # Trade AI BaseSkill 契约（默认配置/权限）
            sa.Column("config_schema_json", sa.Text(), nullable=True),
            sa.Column("default_config_json", sa.Text(), nullable=True),
            sa.Column("permissions_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "status IN (" + ", ".join(f"'{s}'" for s in SKILL_STATUSES) + ")",
                name="ck_skills_status",
            ),
        )
        op.create_index("ix_skills_tenant_name", "skills", ["tenant_id", "name"], unique=True)
        op.create_index("ix_skills_category", "skills", ["category"])

    # ------------------------------------------------------ skill_versions
    if not _table_exists(conn, "skill_versions"):
        op.create_table(
            "skill_versions",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("skill_id", _uuid_col(), sa.ForeignKey("skills.id"), nullable=False),
            sa.Column("version", sa.String(length=40), nullable=False),
            sa.Column("implementation_type", sa.String(length=20), nullable=False, server_default="prompt"),
            sa.Column("implementation_json", sa.Text(), nullable=True),
            sa.Column("input_schema_json", sa.Text(), nullable=True),
            sa.Column("output_schema_json", sa.Text(), nullable=True),
            sa.Column("validators_json", sa.Text(), nullable=True),
            sa.Column("examples_json", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            # 发布门禁痕迹（§1.2-4）
            sa.Column("canary_percent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("approved_by", sa.String(length=36), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("skill_id", "version", name="uq_skill_versions_skill_version"),
        )
        op.create_index("ix_skill_versions_skill", "skill_versions", ["skill_id"])

    # -------------------------------------------------------- mcp_servers
    if not _table_exists(conn, "mcp_servers"):
        op.create_table(
            "mcp_servers",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("endpoint", sa.String(length=500), nullable=True),
            sa.Column("protocol", sa.String(length=30), nullable=True),
            sa.Column("credential_vault_ref", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="disabled"),
            sa.Column("last_health_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_mcp_servers_tenant_name", "mcp_servers", ["tenant_id", "name"], unique=True)

    # ---------------------------------------------------------- mcp_tools
    if not _table_exists(conn, "mcp_tools"):
        op.create_table(
            "mcp_tools",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("server_id", _uuid_col(), sa.ForeignKey("mcp_servers.id"), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("input_schema_json", sa.Text(), nullable=True),
            # 权限精确到 read/write/execute/delete/publish（§4.6-4），默认 NO ACCESS
            sa.Column("permission", sa.String(length=20), nullable=False, server_default="none"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("server_id", "name", name="uq_mcp_tools_server_name"),
        )

    # ------------------------------------------------------------ plugins
    if not _table_exists(conn, "plugins"):
        op.create_table(
            "plugins",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("current_version", sa.String(length=40), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("manifest_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_plugins_tenant_name", "plugins", ["tenant_id", "name"], unique=True)

    # ----------------------------------------------------- plugin_versions
    if not _table_exists(conn, "plugin_versions"):
        op.create_table(
            "plugin_versions",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("plugin_id", _uuid_col(), sa.ForeignKey("plugins.id"), nullable=False),
            sa.Column("version", sa.String(length=40), nullable=False),
            sa.Column("manifest_json", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("plugin_id", "version", name="uq_plugin_versions_plugin_version"),
        )

    # -------------------------------------------- data_source_providers
    # §5.2.4 数据源合规评审清单（取代按供应商拉黑）
    if not _table_exists(conn, "data_source_providers"):
        op.create_table(
            "data_source_providers",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False, unique=True),
            sa.Column("data_class", sa.String(length=30), nullable=False),
            sa.Column("license_basis", sa.String(length=30), nullable=False),
            sa.Column("tos_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("gdpr_category", sa.String(length=30), nullable=True),
            sa.Column("review_status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("review_notes", sa.Text(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint(
                "data_class IN ('public_corporate', 'personal_contact')",
                name="ck_dsp_data_class",
            ),
            sa.CheckConstraint(
                "license_basis IN ('official_api', 'licensed_service', 'scraping')",
                name="ck_dsp_license_basis",
            ),
            sa.CheckConstraint(
                "review_status IN ('pending', 'approved', 'rejected')",
                name="ck_dsp_review_status",
            ),
        )

    # ---------------------------------------------------- tenant 启用开关
    if not _table_exists(conn, "tenant_capability_toggles"):
        op.create_table(
            "tenant_capability_toggles",
            sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), primary_key=True),
            sa.Column("capability_type", sa.String(length=30), primary_key=True),
            sa.Column("capability_id", _uuid_col(), primary_key=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if conn.dialect.name == "postgresql":
        op.execute(
            "COMMENT ON TABLE data_source_providers IS "
            "'数据源合规评审清单（总纲 §5.2.4）。接入前必须登记四项元数据并经评审，裁决权归 Policy Engine。'"
        )


def downgrade() -> None:
    conn = op.get_bind()
    for t in (
        "tenant_capability_toggles",
        "data_source_providers",
        "plugin_versions",
        "plugins",
        "mcp_tools",
        "mcp_servers",
        "skill_versions",
        "skills",
    ):
        if _table_exists(conn, t):
            op.drop_table(t)
