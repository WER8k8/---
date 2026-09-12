"""add tenant custom_domains column

Revision ID: 017_add_tenant_custom_domains
Revises: 4188869502e0
Create Date: 2026-05-21 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '017_add_tenant_custom_domains'
down_revision: Union[str, None] = '4188869502e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tenants',
        sa.Column('custom_domains', sa.Text(), nullable=True, server_default='')
    )


def downgrade() -> None:
    op.drop_column('tenants', 'custom_domains')
