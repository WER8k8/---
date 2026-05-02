"""add keyword ranking tables

Revision ID: 009_add_keyword_ranking_tables
Revises: 008_add_compliance_tables
Create Date: 2026-05-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_keyword_ranking_tables'
down_revision = '008_add_compliance_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 创建关键词排名表
    op.create_table(
        'keyword_rankings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=200), nullable=False),
        sa.Column('search_engine', sa.String(length=50), nullable=False, server_default='baidu'),
        sa.Column('target_url', sa.String(length=500), server_default=''),
        sa.Column('current_position', sa.Integer(), nullable=True),
        sa.Column('previous_position', sa.Integer(), nullable=True),
        sa.Column('best_position', sa.Integer(), nullable=True),
        sa.Column('search_volume', sa.Integer(), server_default='0'),
        sa.Column('difficulty', sa.String(length=20), server_default='medium'),
        sa.Column('cpc', sa.Float(), server_default='0.0'),
        sa.Column('is_tracking', sa.Boolean(), server_default='true'),
        sa.Column('category', sa.String(length=100), server_default=''),
        sa.Column('notes', sa.String(length=500), server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_keyword_search_engine', 'keyword_rankings', ['keyword', 'search_engine'])
    op.create_index('idx_current_position', 'keyword_rankings', ['current_position'])

    # 创建关键词排名历史表
    op.create_table(
        'keyword_ranking_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('keyword_ranking_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=200), nullable=False),
        sa.Column('search_engine', sa.String(length=50), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('search_volume', sa.Integer(), server_default='0'),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['keyword_ranking_id'], ['keyword_rankings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_keyword_date', 'keyword_ranking_history', ['keyword', 'checked_at'])
    op.create_index('idx_history_checked_at', 'keyword_ranking_history', ['checked_at'])

    # 创建SEO竞争对手表
    op.create_table(
        'seo_competitors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=200), server_default=''),
        sa.Column('authority_score', sa.Integer(), server_default='0'),
        sa.Column('backlinks_count', sa.Integer(), server_default='0'),
        sa.Column('organic_keywords', sa.Integer(), server_default='0'),
        sa.Column('organic_traffic', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('notes', sa.String(length=500), server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )
    op.create_index('idx_domain', 'seo_competitors', ['domain'])


def downgrade():
    op.drop_index('idx_domain', table_name='seo_competitors')
    op.drop_table('seo_competitors')
    op.drop_index('idx_history_checked_at', table_name='keyword_ranking_history')
    op.drop_index('idx_history_keyword_date', table_name='keyword_ranking_history')
    op.drop_table('keyword_ranking_history')
    op.drop_index('idx_current_position', table_name='keyword_rankings')
    op.drop_index('idx_keyword_search_engine', table_name='keyword_rankings')
    op.drop_table('keyword_rankings')
