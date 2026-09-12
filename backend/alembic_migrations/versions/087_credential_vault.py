"""087: credential vault（credentials + credential_grants；轮20）

Revision ID: 087
Revises: 083_2
Create Date: 2026-09-02

总纲 §8 087_credential_vault：credentials（SM4/gm_crypto，AAD 四元绑定：
租户/属主/连接/工件）+ 授权关系。

红线（同轮18/19）：STRICT CHECK 仅落在迁移层（PG），ORM 模型只加可移植列，
保证 SQLite 冒烟/开发可用。租户字段与索引必备（执行约束）。

依赖链重新接点：090_pipeline_core.down_revision 由 '083_2' 改为 '087'，
保持 082 -> 083 -> 083_1 -> 083_2 -> 087 -> 090 -> ... 线性链。
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
revision: str = '087'
down_revision: Union[str, None] = '083_2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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
            sa.text("SELECT 1 FROM sqlite_master WHERE type='table' AND name = :n"),
            {"n": name},
        ).fetchone()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "credentials"):
        op.create_table(
            "credentials",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=True),
            sa.Column("owner_type", sa.String(length=40), nullable=False),
            sa.Column("owner_id", sa.String(length=64), nullable=False),
            sa.Column("connection_type", sa.String(length=40), nullable=False),
            sa.Column("connection_id", sa.String(length=64), nullable=False, server_default=""),
            sa.Column("artifact_type", sa.String(length=40), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("ciphertext", sa.Text(), nullable=False),
            sa.Column("aad_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("crypto_backend", sa.String(length=20), nullable=False, server_default="aes_gcm"),
            sa.Column("key_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("rotated_from_id", sa.String(length=36), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_credentials_tenant_id", "credentials", ["tenant_id"]
        )
        op.create_index(
            "ix_credentials_owner", "credentials", ["owner_type", "owner_id"]
        )
        op.create_index(
            "ix_credentials_connection", "credentials", ["connection_type", "connection_id"]
        )

    if not _table_exists(conn, "credential_grants"):
        op.create_table(
            "credential_grants",
            sa.Column("id", _uuid_col(), primary_key=True),
            sa.Column("tenant_id", sa.String(length=36), nullable=True),
            sa.Column("credential_id", sa.String(length=36), nullable=False),
            sa.Column("grantee_type", sa.String(length=20), nullable=False),
            sa.Column("grantee_id", sa.String(length=64), nullable=False),
            sa.Column("scope_json", sa.Text(), nullable=True),
            sa.Column("granted_by", sa.String(length=64), nullable=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        )
        op.create_index(
            "ix_credential_grants_tenant_id", "credential_grants", ["tenant_id"]
        )
        op.create_index(
            "ix_credential_grants_credential_id", "credential_grants", ["credential_id"]
        )
        op.create_index(
            "ix_credential_grants_grantee",
            "credential_grants",
            ["grantee_type", "grantee_id"],
        )

    # ------------------------------------------------ PG 侧 STRICT CHECK
    dialect = conn.dialect.name
    if dialect == "postgresql":
        if _table_exists(conn, "credentials"):
            op.create_check_constraint(
                "ck_credentials_status",
                "credentials",
                "status IN ('active', 'rotated', 'revoked')",
            )
            op.create_check_constraint(
                "ck_credentials_crypto_backend",
                "credentials",
                "crypto_backend IN ('aes_gcm', 'sm4')",
            )
            op.create_check_constraint(
                "ck_credentials_owner_type",
                "credentials",
                "owner_type IN ('tenant', 'agent', 'user', 'plugin', 'mcp_server', 'channel_account')",
            )
            op.create_check_constraint(
                "ck_credentials_artifact_type",
                "credentials",
                "artifact_type IN ('api_key', 'api_token', 'password', "
                "'oauth_refresh_token', 'oauth_client_secret', 'webhook_secret', 'sm2_private_key')",
            )
        if _table_exists(conn, "credential_grants"):
            op.create_check_constraint(
                "ck_credential_grants_status",
                "credential_grants",
                "status IN ('active', 'revoked')",
            )
            op.create_check_constraint(
                "ck_credential_grants_grantee_type",
                "credential_grants",
                "grantee_type IN ('agent', 'skill', 'service', 'user')",
            )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == "postgresql":
        for table, names in (
            ("credential_grants", ("ck_credential_grants_grantee_type", "ck_credential_grants_status")),
            ("credentials", ("ck_credentials_artifact_type", "ck_credentials_owner_type", "ck_credentials_crypto_backend", "ck_credentials_status")),
        ):
            if _table_exists(conn, table):
                for name in names:
                    op.drop_constraint(name, table, type_="check")
    if _table_exists(conn, "credential_grants"):
        op.drop_index("ix_credential_grants_grantee", table_name="credential_grants")
        op.drop_index("ix_credential_grants_credential_id", table_name="credential_grants")
        op.drop_index("ix_credential_grants_tenant_id", table_name="credential_grants")
        op.drop_table("credential_grants")
    if _table_exists(conn, "credentials"):
        op.drop_index("ix_credentials_connection", table_name="credentials")
        op.drop_index("ix_credentials_owner", table_name="credentials")
        op.drop_index("ix_credentials_tenant_id", table_name="credentials")
        op.drop_table("credentials")
