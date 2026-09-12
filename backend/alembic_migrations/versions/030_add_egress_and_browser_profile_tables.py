"""Add egress_endpoints and browser_profiles tables

Revision ID: 030
Revises: 029_add_ai_template_table
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
revision = '030_add_egress_and_browser_profile'
down_revision = '029_add_ai_template_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create egress_endpoints table
    op.create_table(
        'egress_endpoints',
        sa.Column('id', _uuid_col(), primary_key=True),
        sa.Column('region', sa.String(20), nullable=False, index=True),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), default=0),
        sa.Column('provider', sa.String(100)),
        sa.Column('slot_status', sa.String(20), default='available'),
        sa.Column('tenant_id', _uuid_col(), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('label', sa.String(200)),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'platform_accounts',
        sa.Column('id', _uuid_col(), primary_key=True),
        sa.Column('tenant_id', _uuid_col(), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('platform_id', sa.String(50), nullable=False, index=True),
        sa.Column('account_name', sa.String(200), nullable=False),
        sa.Column('credentials', sa.JSON(), default='{}'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create browser_profiles table
    op.create_table(
        'browser_profiles',
        sa.Column('id', _uuid_col(), primary_key=True),
        sa.Column('tenant_id', _uuid_col(), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('egress_endpoint_id', _uuid_col(), sa.ForeignKey('egress_endpoints.id'), nullable=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('fingerprint', sa.JSON(), default='{}'),
        sa.Column('platform_account_id', _uuid_col(), sa.ForeignKey('platform_accounts.id'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('browser_profiles')
    op.drop_table('platform_accounts')
    op.drop_table('egress_endpoints')
