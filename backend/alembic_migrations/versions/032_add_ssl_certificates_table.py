"""Add ssl_certificates table

Revision ID: 032
Revises: 031_add_publish_task_table
Create Date: 2026-05-27
"""
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '032_add_ssl_certificates'
down_revision = '031_add_publish_task'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ssl_certificates table
    op.create_table(
        'ssl_certificates',
        sa.Column('id', _uuid_col(), primary_key=True),
        sa.Column('tenant_id', _uuid_col(), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('domain', sa.String(255), nullable=False, index=True),
        sa.Column('certificate', sa.Text(), nullable=True),
        sa.Column('private_key', sa.Text(), nullable=True),
        sa.Column('chain', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.String(10), default='true'),
        sa.Column('auto_renew', sa.String(10), default='true'),
        sa.Column('last_renewal_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('renewal_error', sa.Text(), nullable=True),
        sa.Column('challenge_type', sa.String(20), default='dns-01'),
        sa.Column('challenge_token', sa.String(255), nullable=True),
        sa.Column('challenge_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('ssl_certificates')
