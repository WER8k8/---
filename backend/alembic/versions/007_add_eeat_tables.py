"""Add EEAT tables

Revision ID: 007_add_eeat_tables
Revises: 006_add_schema_markup_tables
Create Date: 2024-01-15 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_eeat_tables'
down_revision = '006_add_schema_markup_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 创建作者表
    op.create_table(
        'eeat_authors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('company', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('twitter_url', sa.String(length=255), nullable=True),
        sa.Column('expertise_areas', sa.JSON(), nullable=True),
        sa.Column('credentials', sa.JSON(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eeat_authors_id'), 'eeat_authors', ['id'], unique=False)
    op.create_index(op.f('ix_eeat_authors_is_verified'), 'eeat_authors', ['is_verified'], unique=False)
    op.create_index(op.f('ix_eeat_authors_name'), 'eeat_authors', ['name'], unique=False)

    # 创建作者认证表
    op.create_table(
        'eeat_author_certifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=True),
        sa.Column('certification_name', sa.String(length=200), nullable=False),
        sa.Column('issuing_body', sa.String(length=200), nullable=True),
        sa.Column('issue_date', sa.DateTime(), nullable=True),
        sa.Column('expiration_date', sa.DateTime(), nullable=True),
        sa.Column('credential_number', sa.String(length=100), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['eeat_authors.id'], ),
    )
    op.create_index(op.f('ix_eeat_author_certifications_id'), 'eeat_author_certifications', ['id'], unique=False)
    op.create_index(op.f('ix_eeat_author_certifications_author_id'), 'eeat_author_certifications', ['author_id'], unique=False)

    # 创建文章-作者关联表
    op.create_table(
        'eeat_article_authors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('article_id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=True),
        sa.Column('author_type', sa.String(length=50), nullable=True),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['eeat_authors.id'], ),
    )
    op.create_index(op.f('ix_eeat_article_authors_id'), 'eeat_article_authors', ['id'], unique=False)
    op.create_index(op.f('ix_eeat_article_authors_article_id'), 'eeat_article_authors', ['article_id'], unique=False)
    op.create_index(op.f('ix_eeat_article_authors_author_id'), 'eeat_article_authors', ['author_id'], unique=False)

    # 创建EEAT评分表
    op.create_table(
        'eeat_scores',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('content_id', sa.String(length=36), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('experience_score', sa.Float(), nullable=True),
        sa.Column('expertise_score', sa.Float(), nullable=True),
        sa.Column('authoritativeness_score', sa.Float(), nullable=True),
        sa.Column('trustworthiness_score', sa.Float(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('factors', sa.JSON(), nullable=True),
        sa.Column('recommendations', sa.JSON(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eeat_scores_id'), 'eeat_scores', ['id'], unique=False)
    op.create_index(op.f('ix_eeat_scores_content_id'), 'eeat_scores', ['content_id'], unique=False)
    op.create_index(op.f('ix_eeat_scores_content_type'), 'eeat_scores', ['content_type'], unique=False)

    # 创建信任信号表
    op.create_table(
        'eeat_trust_signals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('content_id', sa.String(length=36), nullable=False),
        sa.Column('signal_type', sa.String(length=100), nullable=False),
        sa.Column('signal_value', sa.String(length=500), nullable=True),
        sa.Column('score_impact', sa.Float(), nullable=True),
        sa.Column('is_positive', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eeat_trust_signals_id'), 'eeat_trust_signals', ['id'], unique=False)
    op.create_index(op.f('ix_eeat_trust_signals_content_id'), 'eeat_trust_signals', ['content_id'], unique=False)
    op.create_index(op.f('ix_eeat_trust_signals_signal_type'), 'eeat_trust_signals', ['signal_type'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_eeat_trust_signals_signal_type'), table_name='eeat_trust_signals')
    op.drop_index(op.f('ix_eeat_trust_signals_content_id'), table_name='eeat_trust_signals')
    op.drop_index(op.f('ix_eeat_trust_signals_id'), table_name='eeat_trust_signals')
    op.drop_table('eeat_trust_signals')
    
    op.drop_index(op.f('ix_eeat_scores_content_type'), table_name='eeat_scores')
    op.drop_index(op.f('ix_eeat_scores_content_id'), table_name='eeat_scores')
    op.drop_index(op.f('ix_eeat_scores_id'), table_name='eeat_scores')
    op.drop_table('eeat_scores')
    
    op.drop_index(op.f('ix_eeat_article_authors_author_id'), table_name='eeat_article_authors')
    op.drop_index(op.f('ix_eeat_article_authors_article_id'), table_name='eeat_article_authors')
    op.drop_index(op.f('ix_eeat_article_authors_id'), table_name='eeat_article_authors')
    op.drop_table('eeat_article_authors')
    
    op.drop_index(op.f('ix_eeat_author_certifications_author_id'), table_name='eeat_author_certifications')
    op.drop_index(op.f('ix_eeat_author_certifications_id'), table_name='eeat_author_certifications')
    op.drop_table('eeat_author_certifications')
    
    op.drop_index(op.f('ix_eeat_authors_name'), table_name='eeat_authors')
    op.drop_index(op.f('ix_eeat_authors_is_verified'), table_name='eeat_authors')
    op.drop_index(op.f('ix_eeat_authors_id'), table_name='eeat_authors')
    op.drop_table('eeat_authors')
