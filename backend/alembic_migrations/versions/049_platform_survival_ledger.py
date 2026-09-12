"""平台生存基金台账（超管独享真钱）

Revision ID: 049_platform_survival_ledger
Revises: 048_content_master_preflight
"""

from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa
from sqlalchemy import inspect

revision = "049_platform_survival_ledger"
down_revision = "048_content_master_preflight"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    if _has_table("platform_survival_ledger_entries"):
        return
    op.create_table(
        "platform_survival_ledger_entries",
        sa.Column("id", _uuid_col(), primary_key=True),
        sa.Column("wallet_scope", sa.String(32), nullable=False, server_default="platform_survival"),
        sa.Column("entry_type", sa.String(20), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="CNY"),
        sa.Column("amount_base_minor", sa.Integer(), nullable=False),
        sa.Column("base_currency", sa.String(10), nullable=False, server_default="CNY"),
        sa.Column("fx_rate_to_base", sa.String(24), nullable=False, server_default="1"),
        sa.Column("payment_provider", sa.String(40), nullable=True),
        sa.Column("provider_payment_id", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="settled"),
        sa.Column("opportunity_id", sa.String(100), nullable=True),
        sa.Column("ecc_verdict", sa.String(20), nullable=True),
        sa.Column("recorded_by_user_id", sa.String(36), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "payment_provider",
            "provider_payment_id",
            name="uq_platform_survival_provider_payment",
        ),
    )
    op.create_index(
        "ix_platform_survival_wallet_scope",
        "platform_survival_ledger_entries",
        ["wallet_scope"],
    )
    op.create_index(
        "ix_platform_survival_entry_type",
        "platform_survival_ledger_entries",
        ["entry_type"],
    )
    op.create_index(
        "ix_platform_survival_recorded_at",
        "platform_survival_ledger_entries",
        ["recorded_at"],
    )


def downgrade() -> None:
    if _has_table("platform_survival_ledger_entries"):
        op.drop_table("platform_survival_ledger_entries")
