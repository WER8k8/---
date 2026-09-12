"""egress JIT provision jobs + endpoint proxy fields

Revision ID: 042_egress_jit_provision
Revises: 041_ai_model_sort_order
Create Date: 2026-06-04
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "042_egress_jit_provision"
down_revision = "041_ai_model_sort_order"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "egress_endpoints",
        sa.Column("upstream_ref", sa.String(200), nullable=True),
    )
    op.add_column(
        "egress_endpoints",
        sa.Column("proxy_username", sa.String(200), nullable=True),
    )
    op.add_column(
        "egress_endpoints",
        sa.Column("proxy_password", sa.String(200), nullable=True),
    )
    op.add_column("egress_endpoints", sa.Column("qc_meta", sa.JSON(), nullable=True))
    op.add_column(
        "egress_endpoints",
        sa.Column("provision_error", sa.String(500), nullable=True),
    )

    op.create_table(
        "egress_provision_jobs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column(
            "tenant_id",
            _uuid_col(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "endpoint_id",
            _uuid_col(),
            sa.ForeignKey("egress_endpoints.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.String(50), nullable=False, server_default="mock"),
        sa.Column("region", sa.String(20), nullable=False, server_default="global"),
        sa.Column("country", sa.String(10), nullable=False, server_default="US"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="queued",
            index=True,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("upstream_ref", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("egress_provision_jobs")
    op.drop_column("egress_endpoints", "provision_error")
    op.drop_column("egress_endpoints", "qc_meta")
    op.drop_column("egress_endpoints", "proxy_password")
    op.drop_column("egress_endpoints", "proxy_username")
    op.drop_column("egress_endpoints", "upstream_ref")
