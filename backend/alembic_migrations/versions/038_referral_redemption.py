"""referral cash coupon redemption fields

Revision ID: 038_referral_redemption
Revises: 037_payment_ops_audit
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa

revision = "038_referral_redemption"
down_revision = "037_payment_ops_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "referral_records" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("referral_records")}
    if "redemption_status" not in cols:
        op.add_column(
            "referral_records",
            sa.Column("redemption_status", sa.String(32), nullable=True),
        )
    if "redeemed_at" not in cols:
        op.add_column(
            "referral_records",
            sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "redeem_note" not in cols:
        op.add_column(
            "referral_records",
            sa.Column("redeem_note", sa.String(500), nullable=True),
        )
    idx_names = {i["name"] for i in insp.get_indexes("referral_records")}
    if "ix_referral_records_redemption_status" not in idx_names:
        op.create_index(
            "ix_referral_records_redemption_status",
            "referral_records",
            ["redemption_status"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "referral_records" not in insp.get_table_names():
        return
    idx_names = {i["name"] for i in insp.get_indexes("referral_records")}
    if "ix_referral_records_redemption_status" in idx_names:
        op.drop_index("ix_referral_records_redemption_status", table_name="referral_records")
    cols = {c["name"] for c in insp.get_columns("referral_records")}
    if "redeem_note" in cols:
        op.drop_column("referral_records", "redeem_note")
    if "redeemed_at" in cols:
        op.drop_column("referral_records", "redeemed_at")
    if "redemption_status" in cols:
        op.drop_column("referral_records", "redemption_status")
