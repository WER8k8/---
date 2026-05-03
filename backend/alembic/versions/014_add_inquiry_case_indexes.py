"""add performance indexes for inquiries and case_studies

Revision ID: 014_add_inquiry_case_indexes
Revises: 013_add_content_indexes
Create Date: 2026-05-03 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '014_add_inquiry_case_indexes'
down_revision = '013_add_content_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    inquiry_indexes = [idx['name'] for idx in inspector.get_indexes('inquiries')]
    
    if 'ix_inquiries_status' not in inquiry_indexes:
        op.create_index('ix_inquiries_status', 'inquiries', ['status'])
    
    if 'ix_inquiries_is_active' not in inquiry_indexes:
        op.create_index('ix_inquiries_is_active', 'inquiries', ['is_active'])
    
    if 'ix_inquiries_created_at' not in inquiry_indexes:
        op.create_index('ix_inquiries_created_at', 'inquiries', ['created_at'])
    
    if 'idx_inquiries_status_active' not in inquiry_indexes:
        op.create_index('idx_inquiries_status_active', 'inquiries', ['status', 'is_active'])
    
    case_indexes = [idx['name'] for idx in inspector.get_indexes('case_studies')]
    
    if 'ix_case_studies_status' not in case_indexes:
        op.create_index('ix_case_studies_status', 'case_studies', ['status'])
    
    if 'ix_case_studies_is_active' not in case_indexes:
        op.create_index('ix_case_studies_is_active', 'case_studies', ['is_active'])
    
    if 'ix_case_studies_slug' not in case_indexes:
        op.create_index('ix_case_studies_slug', 'case_studies', ['slug'])
    
    if 'idx_cases_status_active' not in case_indexes:
        op.create_index('idx_cases_status_active', 'case_studies', ['status', 'is_active'])


def downgrade() -> None:
    op.drop_index('idx_cases_status_active', table_name='case_studies')
    op.drop_index('ix_case_studies_slug', table_name='case_studies')
    op.drop_index('ix_case_studies_is_active', table_name='case_studies')
    op.drop_index('ix_case_studies_status', table_name='case_studies')
    op.drop_index('idx_inquiries_status_active', table_name='inquiries')
    op.drop_index('ix_inquiries_created_at', table_name='inquiries')
    op.drop_index('ix_inquiries_is_active', table_name='inquiries')
    op.drop_index('ix_inquiries_status', table_name='inquiries')
