"""add product_id to case_studies (batch mode)

Revision ID: 004
Revises: 003
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_case_product_relation'
down_revision = '003_add_case_studies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("case_studies") as batch_op:
        batch_op.add_column(sa.Column('product_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('project_address', sa.String(255), nullable=True))

    with op.batch_alter_table("case_images") as batch_op:
        pass


def downgrade() -> None:
    pass
