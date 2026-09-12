"""Foreign trade P0: UTM attribution, MEDDPICC, publish_task UTM

Revision ID: 040_foreign_trade_p0
Revises: 039_hermes_plugin_installs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "040_foreign_trade_p0"
down_revision = "039_hermes_plugin_installs"
branch_labels = None
depends_on = None


def _col_names(table: str) -> set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    inq_cols = _col_names("inquiries")
    if inq_cols:
        with op.batch_alter_table("inquiries") as batch:
            if "source_utm" not in inq_cols:
                batch.add_column(sa.Column("source_utm", sa.Text(), nullable=True))
            if "publish_task_id" not in inq_cols:
                batch.add_column(sa.Column("publish_task_id", sa.String(36), nullable=True))
            if "meddpicc_json" not in inq_cols:
                batch.add_column(sa.Column("meddpicc_json", sa.Text(), nullable=True))
        if "publish_task_id" not in inq_cols:
            op.create_index("ix_inquiries_publish_task_id", "inquiries", ["publish_task_id"])

    pt_cols = _col_names("publish_tasks")
    if pt_cols:
        with op.batch_alter_table("publish_tasks") as batch:
            if "tenant_id" not in pt_cols:
                batch.add_column(sa.Column("tenant_id", sa.String(36), nullable=True))
            if "utm_source" not in pt_cols:
                batch.add_column(sa.Column("utm_source", sa.String(120), nullable=True))
            if "utm_medium" not in pt_cols:
                batch.add_column(sa.Column("utm_medium", sa.String(120), nullable=True))
            if "utm_campaign" not in pt_cols:
                batch.add_column(sa.Column("utm_campaign", sa.String(200), nullable=True))
            if "utm_content" not in pt_cols:
                batch.add_column(sa.Column("utm_content", sa.String(200), nullable=True))
        if "utm_campaign" not in pt_cols:
            op.create_index("ix_publish_tasks_utm_campaign", "publish_tasks", ["utm_campaign"])


def downgrade() -> None:
    pt_cols = _col_names("publish_tasks")
    if pt_cols and "utm_campaign" in pt_cols:
        op.drop_index("ix_publish_tasks_utm_campaign", table_name="publish_tasks")
        with op.batch_alter_table("publish_tasks") as batch:
            for col in ("utm_content", "utm_campaign", "utm_medium", "utm_source", "tenant_id"):
                if col in pt_cols:
                    batch.drop_column(col)

    inq_cols = _col_names("inquiries")
    if inq_cols and "publish_task_id" in inq_cols:
        op.drop_index("ix_inquiries_publish_task_id", table_name="inquiries")
        with op.batch_alter_table("inquiries") as batch:
            for col in ("meddpicc_json", "publish_task_id", "source_utm"):
                if col in inq_cols:
                    batch.drop_column(col)
