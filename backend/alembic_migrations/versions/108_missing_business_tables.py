"""108: create five referenced business tables whose models were unregistered.

The service layer has referenced wallet, token-ledger, email-outreach and
agent-commission tables for some time, but their ORM classes were never
registered and no create-table migration existed.  This migration closes that
schema gap without changing any service contract.

Revision ID: 108_missing_business_tables
Revises: 107_reconcile_uuid_column_types
Create Date: 2026-09-11
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "108_missing_business_tables"
down_revision: Union[str, None] = "107_reconcile_uuid_column_types"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


EMAIL_STATUSES = (
    "draft",
    "queued",
    "sending",
    "sent",
    "delivered",
    "opened",
    "clicked",
    "bounced",
    "complained",
    "unsubscribed",
    "failed",
    "cancelled",
)
BOUNCE_TYPES = ("hard", "soft")


def _uuid_col():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


def _create_email_enums() -> None:
    if op.get_context().dialect.name != "postgresql":
        return

    statuses = ", ".join(f"'{status}'" for status in EMAIL_STATUSES)
    bounces = ", ".join(f"'{bounce}'" for bounce in BOUNCE_TYPES)
    op.execute(
        f"""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'email_status_enum') THEN
                CREATE TYPE email_status_enum AS ENUM ({statuses});
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'bounce_type_enum') THEN
                CREATE TYPE bounce_type_enum AS ENUM ({bounces});
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    _create_email_enums()

    op.create_table(
        "wallet_accounts",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CNY"),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "currency", name="uq_wallet_account_user_currency"),
    )
    op.create_index("ix_wallet_accounts_user_id", "wallet_accounts", ["user_id"])

    op.create_table(
        "wallet_transactions",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tx_id", sa.String(32), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CNY"),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("to_user_id", sa.String(64), nullable=True),
        sa.Column("ref_type", sa.String(50), nullable=True),
        sa.Column("ref_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_wallet_transactions_tx_id", "wallet_transactions", ["tx_id"], unique=True)
    op.create_index("ix_wallet_transactions_user_id", "wallet_transactions", ["user_id"])
    op.create_index("ix_wallet_transactions_ref_id", "wallet_transactions", ["ref_id"])
    op.create_index("ix_wallet_transactions_created_at", "wallet_transactions", ["created_at"])

    op.create_table(
        "token_ledger_entries",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("tenant_id", _uuid_col(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_token_ledger_entries_tenant_id", "token_ledger_entries", ["tenant_id"])
    op.create_index("ix_token_ledger_entries_created_at", "token_ledger_entries", ["created_at"])

    op.create_table(
        "agent_commission_settlements",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("agent_node_id", _uuid_col(), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("revenue_cents", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("commission_cents", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("commission_rate_bp", sa.Integer(), nullable=True, server_default="1000"),
        sa.Column("status", sa.String(20), nullable=True, server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_agent_commission_settlements_agent_node_id", "agent_commission_settlements", ["agent_node_id"])
    op.create_index("ix_agent_commission_settlements_period", "agent_commission_settlements", ["period"])

    email_status = sa.Enum(*EMAIL_STATUSES, name="email_status_enum", create_type=False)
    bounce_type = sa.Enum(*BOUNCE_TYPES, name="bounce_type_enum", create_type=False)
    from sqlalchemy.dialects.postgresql import ENUM

    email_status = ENUM(*EMAIL_STATUSES, name="email_status_enum", create_type=False)
    bounce_type = ENUM(*BOUNCE_TYPES, name="bounce_type_enum", create_type=False)
    op.create_table(
        "email_outreachs",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.Column("tenant_id", _uuid_col(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("user_id", _uuid_col(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("from_email", sa.String(255), nullable=False),
        sa.Column("from_name", sa.String(255), nullable=False, server_default="优丁出海"),
        sa.Column("to_email", sa.String(255), nullable=False),
        sa.Column("reply_to", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column("status", email_status, nullable=False, server_default="draft"),
        sa.Column("sequence_id", sa.String(64), nullable=True),
        sa.Column("sequence_step", sa.Integer(), nullable=True),
        sa.Column("sequence_total_steps", sa.Integer(), nullable=True),
        sa.Column("tracking_pixel_id", sa.String(64), nullable=True),
        sa.Column("tracking_links", sa.JSON(), nullable=True),
        sa.Column("open_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bounce_type", bounce_type, nullable=True),
        sa.Column("bounce_reason", sa.String(500), nullable=True),
        sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(32), nullable=True),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("outreach_metadata", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_email_outreachs_idempotency_key", "email_outreachs", ["idempotency_key"], unique=True)
    op.create_index("ix_email_outreachs_tenant_id", "email_outreachs", ["tenant_id"])
    op.create_index("ix_email_outreachs_user_id", "email_outreachs", ["user_id"])
    op.create_index("ix_email_outreachs_to_email", "email_outreachs", ["to_email"])
    op.create_index("ix_email_outreachs_status", "email_outreachs", ["status"])
    op.create_index("ix_email_outreachs_sequence_id", "email_outreachs", ["sequence_id"])
    op.create_index("ix_email_outreachs_tracking_pixel_id", "email_outreachs", ["tracking_pixel_id"], unique=True)
    op.create_index("ix_email_outreachs_created_at", "email_outreachs", ["created_at"])
    op.create_index("idx_email_outreach_tenant_status", "email_outreachs", ["tenant_id", "status"])
    op.create_index("idx_email_outreach_sequence", "email_outreachs", ["sequence_id", "sequence_step"])
    op.create_index("idx_email_outreach_to_status", "email_outreachs", ["to_email", "status"])


def downgrade() -> None:
    for name in (
        "idx_email_outreach_to_status",
        "idx_email_outreach_sequence",
        "idx_email_outreach_tenant_status",
        "ix_email_outreachs_created_at",
        "ix_email_outreachs_tracking_pixel_id",
        "ix_email_outreachs_sequence_id",
        "ix_email_outreachs_status",
        "ix_email_outreachs_to_email",
        "ix_email_outreachs_user_id",
        "ix_email_outreachs_tenant_id",
        "ix_email_outreachs_idempotency_key",
    ):
        op.drop_index(name, table_name="email_outreachs")
    op.drop_table("email_outreachs")

    op.drop_index("ix_agent_commission_settlements_period", table_name="agent_commission_settlements")
    op.drop_index("ix_agent_commission_settlements_agent_node_id", table_name="agent_commission_settlements")
    op.drop_table("agent_commission_settlements")

    op.drop_index("ix_token_ledger_entries_created_at", table_name="token_ledger_entries")
    op.drop_index("ix_token_ledger_entries_tenant_id", table_name="token_ledger_entries")
    op.drop_table("token_ledger_entries")

    op.drop_index("ix_wallet_transactions_created_at", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_ref_id", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_user_id", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_tx_id", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index("ix_wallet_accounts_user_id", table_name="wallet_accounts")
    op.drop_table("wallet_accounts")

    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS bounce_type_enum;")
        op.execute("DROP TYPE IF EXISTS email_status_enum;")
