"""ai model config sort_order for fallback ranking

Revision ID: 041_ai_model_sort_order
Revises: 040_platform_tenant_origins
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa

revision = "041_ai_model_sort_order"
down_revision = "040_platform_tenant_origins"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 幂等化（102 同款模式）：存量库 ai_model_configs 可能已有 sort_order 列，
    # 裸 add_column 会让整条迁移链在真实库上无法推进。
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = {c["name"] for c in insp.get_columns("ai_model_configs")}
    existing_idx = {i["name"] for i in insp.get_indexes("ai_model_configs")}

    if "sort_order" not in existing_cols:
        op.add_column(
            "ai_model_configs",
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        )
    if op.f("ix_ai_model_configs_sort_order") not in existing_idx:
        op.create_index(
            op.f("ix_ai_model_configs_sort_order"),
            "ai_model_configs",
            ["sort_order"],
            unique=False,
        )

    rows = conn.execute(
        sa.text(
            """
            SELECT id, provider_id
            FROM ai_model_configs
            ORDER BY provider_id, is_default DESC, created_at ASC
            """
        )
    ).fetchall()
    rank_by_provider: dict[str, int] = {}
    for row in rows:
        pid = str(row.provider_id)
        rank_by_provider[pid] = rank_by_provider.get(pid, 0) + 1
        conn.execute(
            sa.text("UPDATE ai_model_configs SET sort_order = :n WHERE id = :id"),
            {"n": rank_by_provider[pid], "id": str(row.id)},
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_model_configs_sort_order"), table_name="ai_model_configs")
    op.drop_column("ai_model_configs", "sort_order")
