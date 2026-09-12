"""083.1: skills 表补字段 + 版本表校验约束（轮18）

Revision ID: 083_1
Revises: 083
Create Date: 2026-09-02

总纲 §A.2（轮18）：
- skills 补 priority/timeout/retry_count/retry_delay（对齐 Trade AI BaseSkill 与
  GoodJob skill.json 运行字段缺口）；
- skill_versions 补 tool_refs_json（版本级工具绑定，Array-of-String）并对其加
  CHECK（PG：json 数组且元素均为 string）；
- skill_versions.validators_json 加 CHECK（PG：必须含 lifecycle 钩子
  on_start/on_success/on_failure/on_skip）。

红线（§A.2）：不破坏 083 原字段；不加 skills.tenant_id NOT NULL；
不加 skills.source_type CHECK。STRICT JSON CHECK 仅落在迁移层（PG），
ORM 模型只加可移植列，保证 SQLite 冒烟/开发可用。

依赖链重新接点：090_pipeline_core.down_revision 由 '083' 改为 '083_1'，
保持 082 -> 083 -> 083_1 -> 090 -> ... 线性链，避免 alembic 分支。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '083_1'
down_revision: Union[str, None] = '083'
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
            sa.text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name = :n"
            ),
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


def _add_vs_cols(conn, table: str, cols: list) -> None:
    for col in cols:
        if not _column_exists(conn, table, col[0]):
            op.add_column(table, col[1])


def upgrade() -> None:
    conn = op.get_bind()

    # ---------------------------------------------------------- skills 补字段
    _add_vs_cols(
        conn,
        "skills",
        [
            ("priority", sa.Column("priority", sa.Integer(), nullable=False, server_default="50")),
            ("timeout", sa.Column("timeout", sa.Integer(), nullable=True)),
            ("retry_count", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0")),
            ("retry_delay", sa.Column("retry_delay", sa.Integer(), nullable=False, server_default="0")),
        ],
    )

    # --------------------------------------------- skill_versions 补列 + STRICT CHECK
    if _table_exists(conn, "skill_versions") and not _column_exists(conn, "skill_versions", "tool_refs_json"):
        op.add_column("skill_versions", sa.Column("tool_refs_json", sa.Text(), nullable=True))

    dialect = conn.dialect.name
    if dialect == "postgresql":
        if _table_exists(conn, "skill_versions"):
            # 2026-09-03 真 PG 实测修正：PG CHECK 约束禁止子查询（FeatureNotSupported）。
            # 标准做法：IMMUTABLE plpgsql 函数封装子查询，CHECK 只调用函数。
            op.execute("""
                CREATE OR REPLACE FUNCTION js_all_string_elements(j text)
                RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $fn$
                BEGIN
                  IF j IS NULL THEN RETURN true; END IF;
                  IF json_typeof(j::json) <> 'array' THEN RETURN false; END IF;
                  RETURN NOT EXISTS (
                    SELECT 1 FROM json_array_elements(j::json) e
                    WHERE json_typeof(e.value) <> 'string'
                  );
                END $fn$;
            """)
            op.create_check_constraint(
                "ck_skill_versions_tool_refs_array",
                "skill_versions",
                "js_all_string_elements(tool_refs_json)",
            )
            op.create_check_constraint(
                "ck_skill_versions_validators_lifecycle",
                "skill_versions",
                # 2026-09-03 真 PG 实测修正：? 操作符只支持 jsonb，json 列需 ::jsonb
                "validators_json IS NULL OR ("
                "  json_typeof(validators_json::json) = 'object'"
                "  AND validators_json::jsonb ? 'lifecycle'"
                "  AND (validators_json::jsonb -> 'lifecycle') ? 'on_start'"
                "  AND (validators_json::jsonb -> 'lifecycle') ? 'on_success'"
                "  AND (validators_json::jsonb -> 'lifecycle') ? 'on_failure'"
                "  AND (validators_json::jsonb -> 'lifecycle') ? 'on_skip'"
                ")",
            )


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    # 先删约束，再删列（PG 下顺序敏感；SQLite 无这些 CHECK）
    if dialect == "postgresql" and _table_exists(conn, "skill_versions"):
        op.drop_constraint(
            "ck_skill_versions_validators_lifecycle", "skill_versions", type_="check"
        )
        op.drop_constraint(
            "ck_skill_versions_tool_refs_array", "skill_versions", type_="check"
        )
        # 2026-09-03 伴随 CHECK 修正：删掉辅助函数
        op.execute("DROP FUNCTION IF EXISTS js_all_string_elements(text);")
    if _table_exists(conn, "skill_versions") and _column_exists(conn, "skill_versions", "tool_refs_json"):
        op.drop_column("skill_versions", "tool_refs_json")
    # skills 删列
    for col in ("retry_delay", "retry_count", "timeout", "priority"):
        if _table_exists(conn, "skills") and _column_exists(conn, "skills", col):
            op.drop_column("skills", col)