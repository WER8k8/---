"""add content versions table

Revision ID: 012_add_content_versions
Revises: 011_add_performance_indexes
Create Date: 2026-05-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '012_add_content_versions'
down_revision = '011_add_performance_indexes'
branch_labels = None
depends_on = None


def get_id_type():
    """根据数据库类型返回ID字段类型"""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        return sa.dialects.postgresql.UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    id_type = get_id_type()
    
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if 'content_versions' not in inspector.get_table_names():
        op.create_table(
            'content_versions',
            sa.Column('id', id_type, primary_key=True, nullable=False),
            sa.Column('page_id', id_type, sa.ForeignKey('content_pages.id'), nullable=False),
            sa.Column('version_number', sa.Integer, nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('content', sa.Text, nullable=True),
            sa.Column('summary', sa.String(500), nullable=True),
            sa.Column('change_log', sa.String(500), nullable=True),
            sa.Column('author_id', id_type, nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    
    indexes = [idx['name'] for idx in inspector.get_indexes('content_versions')]
    if 'ix_content_versions_page_id' not in indexes:
        op.create_index('ix_content_versions_page_id', 'content_versions', ['page_id'])
    if 'ix_content_versions_version_number' not in indexes:
        op.create_index('ix_content_versions_version_number', 'content_versions', ['version_number'])


def downgrade() -> None:
    op.drop_index('ix_content_versions_version_number')
    op.drop_index('ix_content_versions_page_id')
    op.drop_table('content_versions')
