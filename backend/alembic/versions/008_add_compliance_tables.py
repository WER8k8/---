"""Add compliance tables

Revision ID: 008_add_compliance_tables
Revises: 007_add_eeat_tables
Create Date: 2024-01-15 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_compliance_tables'
down_revision = '007_add_eeat_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 创建合规规则表
    op.create_table(
        'compliance_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_rules_id'), 'compliance_rules', ['id'], unique=False)
    op.create_index(op.f('ix_compliance_rules_rule_type'), 'compliance_rules', ['rule_type'], unique=False)

    # 创建扫描结果表
    op.create_table(
        'compliance_scan_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('content_id', sa.String(length=36), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('content_title', sa.String(length=255), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('scan_status', sa.String(length=20), nullable=False),
        sa.Column('total_issues', sa.Integer(), nullable=True),
        sa.Column('high_severity_count', sa.Integer(), nullable=True),
        sa.Column('medium_severity_count', sa.Integer(), nullable=True),
        sa.Column('low_severity_count', sa.Integer(), nullable=True),
        sa.Column('scan_details', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('scanned_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_scan_results_id'), 'compliance_scan_results', ['id'], unique=False)
    op.create_index(op.f('ix_compliance_scan_results_content_id'), 'compliance_scan_results', ['content_id'], unique=False)

    # 创建违规记录表
    op.create_table(
        'compliance_violations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('scan_result_id', sa.String(length=36), nullable=True),
        sa.Column('rule_id', sa.String(length=36), nullable=True),
        sa.Column('rule_name', sa.String(length=100), nullable=True),
        sa.Column('rule_type', sa.String(length=50), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('matched_text', sa.String(length=255), nullable=True),
        sa.Column('context', sa.String(length=500), nullable=True),
        sa.Column('suggestion', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_violations_id'), 'compliance_violations', ['id'], unique=False)
    op.create_index(op.f('ix_compliance_violations_scan_result_id'), 'compliance_violations', ['scan_result_id'], unique=False)
    op.create_index(op.f('ix_compliance_violations_rule_id'), 'compliance_violations', ['rule_id'], unique=False)

    # 创建广告法违禁词表
    op.create_table(
        'ad_law_keywords',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alternative', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('keyword')
    )
    op.create_index(op.f('ix_ad_law_keywords_id'), 'ad_law_keywords', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ad_law_keywords_id'), table_name='ad_law_keywords')
    op.drop_table('ad_law_keywords')
    
    op.drop_index(op.f('ix_compliance_violations_rule_id'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_scan_result_id'), table_name='compliance_violations')
    op.drop_index(op.f('ix_compliance_violations_id'), table_name='compliance_violations')
    op.drop_table('compliance_violations')
    
    op.drop_index(op.f('ix_compliance_scan_results_content_id'), table_name='compliance_scan_results')
    op.drop_index(op.f('ix_compliance_scan_results_id'), table_name='compliance_scan_results')
    op.drop_table('compliance_scan_results')
    
    op.drop_index(op.f('ix_compliance_rules_rule_type'), table_name='compliance_rules')
    op.drop_index(op.f('ix_compliance_rules_id'), table_name='compliance_rules')
    op.drop_table('compliance_rules')
