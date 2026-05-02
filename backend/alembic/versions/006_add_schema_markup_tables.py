"""Add schema markup tables

Revision ID: 006_add_schema_markup_tables
Revises: 005_specifications_json
Create Date: 2026-05-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_schema_markup_tables'
down_revision = '005_specifications_json'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建schema_markups表
    op.create_table(
        'schema_markups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('schema_type', sa.String(length=100), nullable=False),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_schema_markups_schema_type'), 'schema_markups', ['schema_type'], unique=False)
    
    # 创建schema_templates表
    op.create_table(
        'schema_templates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('schema_type', sa.String(length=100), nullable=False),
        sa.Column('template', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index(op.f('ix_schema_templates_schema_type'), 'schema_templates', ['schema_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_schema_templates_schema_type'), table_name='schema_templates')
    op.drop_table('schema_templates')
    op.drop_index(op.f('ix_schema_markups_schema_type'), table_name='schema_markups')
    op.drop_table('schema_markups')
