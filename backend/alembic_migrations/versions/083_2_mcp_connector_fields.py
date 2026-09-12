"""083.2: mcp_servers 补 connector-manifest 十字段（轮19）

Revision ID: 083_2
Revises: 083_1
Create Date: 2026-09-02

总纲 §A.2（轮19）——对齐 GoodJob integration-sdk ConnectorManifest（v1.0）：
- stage（planned/available）、driver、approved_hosts、allowed_ports、
  allow_insecure_loopback、authentication（none/oauth2/api_token）、
  oauth、credential_fields、max_tools（1-200）、manifest_hash（sha256）；
- endpoint 为 083 既有列，本迁移不重复。

红线（§A.2，同轮18）：不破坏 083/083_1 原字段；STRICT JSON CHECK 仅落在
迁移层（PG），ORM 模型只加可移植列，保证 SQLite 冒烟/开发可用。

依赖链重新接点：090_pipeline_core.down_revision 由 '083_1' 改为 '083_2'，
保持 082 -> 083 -> 083_1 -> 083_2 -> 090 -> ... 线性链，避免 alembic 分支。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '083_2'
down_revision: Union[str, None] = '083_1'
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


def _column_exists(conn, table: str, column: str) -> bool:
    dialect = conn.dialect.name
    if dialect == "postgresql":
        row = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c"
            ),
            {"t": table, "c": column},
        ).fetchone()
    else:
        row = conn.execute(
            sa.text("PRAGMA table_info({})".format(table)),
        ).fetchall()
        return any(r[1] == column for r in row)
    return row is not None


def _add_cols(conn, table: str, cols: list) -> None:
    for col in cols:
        if not _column_exists(conn, table, col[0]):
            op.add_column(table, col[1])


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------ mcp_servers 补十字段
    _add_cols(
        conn,
        "mcp_servers",
        [
            ("stage", sa.Column("stage", sa.String(length=20), nullable=False, server_default="planned")),
            ("driver", sa.Column("driver", sa.String(length=40), nullable=True)),
            ("approved_hosts_json", sa.Column("approved_hosts_json", sa.Text(), nullable=True)),
            ("allowed_ports_json", sa.Column("allowed_ports_json", sa.Text(), nullable=True)),
            (
                "allow_insecure_loopback",
                sa.Column("allow_insecure_loopback", sa.Boolean(), nullable=False, server_default=sa.false()),
            ),
            ("authentication", sa.Column("authentication", sa.String(length=20), nullable=False, server_default="none")),
            ("oauth_json", sa.Column("oauth_json", sa.Text(), nullable=True)),
            ("credential_fields_json", sa.Column("credential_fields_json", sa.Text(), nullable=True)),
            ("max_tools", sa.Column("max_tools", sa.Integer(), nullable=False, server_default="200")),
            ("manifest_hash", sa.Column("manifest_hash", sa.String(length=64), nullable=True)),
        ],
    )

    # ------------------------------------------------ PG 侧 STRICT CHECK
    dialect = conn.dialect.name
    if dialect == "postgresql" and _table_exists(conn, "mcp_servers"):
        # 2026-09-03 真 PG 实测修正：PG CHECK 禁子查询 → IMMUTABLE 函数封装
        # js_all_string_elements 已在 083_1 建；这里补 number 版本
        op.execute("""
            CREATE OR REPLACE FUNCTION js_all_number_elements(j text)
            RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $fn$
            BEGIN
              IF j IS NULL THEN RETURN true; END IF;
              IF json_typeof(j::json) <> 'array' THEN RETURN false; END IF;
              RETURN NOT EXISTS (
                SELECT 1 FROM json_array_elements(j::json) e
                WHERE json_typeof(e.value) <> 'number'
              );
            END $fn$;
        """)
        op.create_check_constraint(
            "ck_mcp_servers_stage",
            "mcp_servers",
            "stage IN ('planned', 'available')",
        )
        op.create_check_constraint(
            "ck_mcp_servers_authentication",
            "mcp_servers",
            "authentication IN ('none', 'oauth2', 'api_token')",
        )
        op.create_check_constraint(
            "ck_mcp_servers_max_tools",
            "mcp_servers",
            "max_tools >= 1 AND max_tools <= 200",
        )
        op.create_check_constraint(
            "ck_mcp_servers_hosts_array",
            "mcp_servers",
            "js_all_string_elements(approved_hosts_json)",
        )
        op.create_check_constraint(
            "ck_mcp_servers_ports_array",
            "mcp_servers",
            "js_all_number_elements(allowed_ports_json)",
        )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    # 先删约束，再删列（PG 下顺序敏感；SQLite 无这些 CHECK）
    if dialect == "postgresql" and _table_exists(conn, "mcp_servers"):
        for name in (
            "ck_mcp_servers_ports_array",
            "ck_mcp_servers_hosts_array",
            "ck_mcp_servers_max_tools",
            "ck_mcp_servers_authentication",
            "ck_mcp_servers_stage",
        ):
            op.drop_constraint(name, "mcp_servers", type_="check")
        # 2026-09-03 伴随 CHECK 修正：删掉辅助函数（js_all_string_elements 归 083_1 管）
        op.execute("DROP FUNCTION IF EXISTS js_all_number_elements(text);")
    for col in (
        "manifest_hash",
        "max_tools",
        "credential_fields_json",
        "oauth_json",
        "authentication",
        "allow_insecure_loopback",
        "allowed_ports_json",
        "approved_hosts_json",
        "driver",
        "stage",
    ):
        if _table_exists(conn, "mcp_servers") and _column_exists(conn, "mcp_servers", col):
            op.drop_column("mcp_servers", col)
