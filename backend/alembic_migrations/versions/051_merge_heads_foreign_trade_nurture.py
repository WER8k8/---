"""merge alembic heads: foreign_trade_p0 + nurture_cycle + paperclip

Revision ID: 051_merge_heads
Revises: 040_foreign_trade_p0, 050_nurture_cycle, 050_paperclip
"""

revision = "051_merge_heads"
down_revision = ("040_foreign_trade_p0", "050_nurture_cycle", "050_paperclip")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
