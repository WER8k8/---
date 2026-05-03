"""add performance indexes to content_pages

Revision ID: 013_add_content_indexes
Revises: 012_add_content_versions
Create Date: 2026-05-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '013_add_content_indexes'
down_revision = '012_add_content_versions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    indexes = [idx['name'] for idx in inspector.get_indexes('content_pages')]
    
    if 'ix_content_pages_status' not in indexes:
        op.create_index('ix_content_pages_status', 'content_pages', ['status'])
    
    if 'ix_content_pages_is_active' not in indexes:
        op.create_index('ix_content_pages_is_active', 'content_pages', ['is_active'])
    
    if 'ix_content_pages_created_at' not in indexes:
        op.create_index('ix_content_pages_created_at', 'content_pages', ['created_at'])
    
    if 'idx_pages_type_status_active' not in indexes:
        op.create_index('idx_pages_type_status_active', 'content_pages', ['page_type', 'status', 'is_active'])


def downgrade() -> None:
    op.drop_index('idx_pages_type_status_active', table_name='content_pages')
    op.drop_index('ix_content_pages_created_at', table_name='content_pages')
    op.drop_index('ix_content_pages_is_active', table_name='content_pages')
    op.drop_index('ix_content_pages_status', table_name='content_pages')
