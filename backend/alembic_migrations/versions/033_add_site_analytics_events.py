"""Add site_analytics_events and inquiry attribution columns

Revision ID: 033_add_site_analytics
Revises: 032_add_ssl_certificates
"""
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "033_add_site_analytics"
down_revision = "032_add_ssl_certificates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_analytics_events",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=True),
        sa.Column("agent_node_id", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("page_path", sa.String(500), nullable=True),
        sa.Column("page_title", sa.String(300), nullable=True),
        sa.Column("element_id", sa.String(200), nullable=True),
        sa.Column("element_label", sa.String(300), nullable=True),
        sa.Column("content_ref", sa.String(200), nullable=True),
        sa.Column("product_id", sa.String(64), nullable=True),
        sa.Column("merchant_id", sa.String(64), nullable=True),
        sa.Column("visitor_country", sa.String(64), nullable=True),
        sa.Column("visitor_language", sa.String(16), nullable=True),
        sa.Column("inquiry_id", sa.String(36), nullable=True),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_site_analytics_events_tenant_id", "site_analytics_events", ["tenant_id"])
    op.create_index("ix_site_analytics_events_session_id", "site_analytics_events", ["session_id"])
    op.create_index("ix_site_analytics_events_event_type", "site_analytics_events", ["event_type"])
    op.create_index("ix_site_analytics_events_created_at", "site_analytics_events", ["created_at"])
    op.create_index(
        "ix_site_analytics_tenant_created",
        "site_analytics_events",
        ["tenant_id", "created_at"],
    )

    # with op.batch_alter_table("inquiries") as batch_op:
    #     batch_op.add_column(sa.Column("session_id", sa.String(64), nullable=True))
    #     batch_op.add_column(sa.Column("landing_path", sa.String(500), nullable=True))
    #     batch_op.add_column(sa.Column("last_click_label", sa.String(300), nullable=True))
    #     batch_op.add_column(sa.Column("tenant_id", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("inquiries") as batch_op:
        batch_op.drop_column("tenant_id")
        batch_op.drop_column("last_click_label")
        batch_op.drop_column("landing_path")
        batch_op.drop_column("session_id")
    op.drop_index("ix_site_analytics_tenant_created", table_name="site_analytics_events")
    op.drop_index("ix_site_analytics_events_created_at", table_name="site_analytics_events")
    op.drop_index("ix_site_analytics_events_event_type", table_name="site_analytics_events")
    op.drop_index("ix_site_analytics_events_session_id", table_name="site_analytics_events")
    op.drop_index("ix_site_analytics_events_tenant_id", table_name="site_analytics_events")
    op.drop_table("site_analytics_events")
