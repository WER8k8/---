"""invoice application tables

Revision ID: 035_invoice_applications
Revises: 034_agent_commission_rules
Create Date: 2026-05-31
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

revision = "035_invoice_applications"
down_revision = "034_agent_commission_rules"
branch_labels = None
depends_on = None


def _user_id_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    op.create_table(
        "platform_invoice_configs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("seller_name", sa.String(200), nullable=False),
        sa.Column("seller_tax_id", sa.String(20), nullable=False),
        sa.Column("seller_address", sa.String(300)),
        sa.Column("seller_phone", sa.String(50)),
        sa.Column("seller_bank_name", sa.String(200)),
        sa.Column("seller_bank_account", sa.String(64)),
        sa.Column("service_category", sa.String(100)),
        sa.Column("disclaimer", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "tenant_invoice_profiles",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("buyer_type", sa.String(20)),
        sa.Column("invoice_type", sa.String(20)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("tax_id", sa.String(20)),
        sa.Column("company_address", sa.String(300)),
        sa.Column("company_phone", sa.String(50)),
        sa.Column("bank_name", sa.String(200)),
        sa.Column("bank_account", sa.String(64)),
        sa.Column("recipient_email", sa.String(200), nullable=False),
        sa.Column("is_default", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_tenant_invoice_profiles_tenant_id", "tenant_invoice_profiles", ["tenant_id"])

    op.create_table(
        "invoice_applications",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("payment_order_id", _uuid_col(), sa.ForeignKey("payment_orders.id"), nullable=False),
        sa.Column("applicant_user_id", _user_id_type(), sa.ForeignKey("users.id")),
        sa.Column("buyer_type", sa.String(20), nullable=False),
        sa.Column("invoice_type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("tax_id", sa.String(20)),
        sa.Column("company_address", sa.String(300)),
        sa.Column("company_phone", sa.String(50)),
        sa.Column("bank_name", sa.String(200)),
        sa.Column("bank_account", sa.String(64)),
        sa.Column("recipient_email", sa.String(200), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("order_no", sa.String(100)),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_review"),
        sa.Column("disclaimer_ack", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reject_reason", sa.Text()),
        sa.Column("admin_note", sa.Text()),
        sa.Column("customer_note", sa.Text()),
        sa.Column("reviewed_by", _user_id_type(), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("invoice_code", sa.String(32)),
        sa.Column("invoice_number", sa.String(32)),
        sa.Column("invoice_file_note", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_invoice_applications_tenant_id", "invoice_applications", ["tenant_id"])
    op.create_index("ix_invoice_applications_payment_order_id", "invoice_applications", ["payment_order_id"])
    op.create_index("ix_invoice_applications_status", "invoice_applications", ["status"])


def downgrade() -> None:
    op.drop_table("invoice_applications")
    op.drop_table("tenant_invoice_profiles")
    op.drop_table("platform_invoice_configs")
