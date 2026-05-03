"""add news_articles and news_categories tables

Revision ID: 015_add_news_tables
Revises: 014_add_inquiry_case_indexes
Create Date: 2026-05-03 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '015_add_news_tables'
down_revision = '014_add_inquiry_case_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'news_articles' not in existing_tables:
        op.create_table(
            'news_articles',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('slug', sa.String(255), unique=True, nullable=False),
            sa.Column('subtitle', sa.String(255), nullable=True),
            sa.Column('summary', sa.Text, nullable=True),
            sa.Column('content', sa.Text, nullable=False),
            sa.Column('cover_image', sa.String(500), nullable=True),
            sa.Column('category', sa.String(50), nullable=False),
            sa.Column('tags', sa.String(500), nullable=True),
            sa.Column('author', sa.String(100), nullable=True),
            sa.Column('source', sa.String(100), nullable=True),
            sa.Column('view_count', sa.Integer, server_default='0'),
            sa.Column('is_published', sa.Boolean, server_default='0'),
            sa.Column('published_at', sa.DateTime, nullable=True),
            sa.Column('sort_order', sa.Integer, server_default='0'),
            sa.Column('is_active', sa.Boolean, server_default='1'),
            sa.Column('meta_title', sa.String(255), nullable=True),
            sa.Column('meta_description', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_news_articles_title', 'news_articles', ['title'])
        op.create_index('ix_news_articles_slug', 'news_articles', ['slug'])
        op.create_index('ix_news_articles_category', 'news_articles', ['category'])
        op.create_index('ix_news_articles_is_published', 'news_articles', ['is_published'])
        op.create_index('ix_news_articles_is_active', 'news_articles', ['is_active'])
        op.create_index('ix_news_articles_created_at', 'news_articles', ['created_at'])
        op.create_index('idx_news_category_published', 'news_articles', ['category', 'is_published'])
    
    if 'news_categories' not in existing_tables:
        op.create_table(
            'news_categories',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('slug', sa.String(100), unique=True, nullable=False),
            sa.Column('description', sa.String(500), nullable=True),
            sa.Column('sort_order', sa.Integer, server_default='0'),
            sa.Column('is_active', sa.Boolean, server_default='1'),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index('ix_news_categories_slug', 'news_categories', ['slug'])


def downgrade() -> None:
    op.drop_index('ix_news_categories_slug', table_name='news_categories')
    op.drop_table('news_categories')
    op.drop_index('idx_news_category_published', table_name='news_articles')
    op.drop_index('ix_news_articles_created_at', table_name='news_articles')
    op.drop_index('ix_news_articles_is_active', table_name='news_articles')
    op.drop_index('ix_news_articles_is_published', table_name='news_articles')
    op.drop_index('ix_news_articles_category', table_name='news_articles')
    op.drop_index('ix_news_articles_slug', table_name='news_articles')
    op.drop_index('ix_news_articles_title', table_name='news_articles')
    op.drop_table('news_articles')
