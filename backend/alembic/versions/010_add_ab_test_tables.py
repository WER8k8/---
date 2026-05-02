"""add ab test tables

Revision ID: 010_add_ab_test_tables
Revises: 009_add_keyword_ranking_tables
Create Date: 2026-05-02 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_ab_test_tables'
down_revision = '009_add_keyword_ranking_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ABTest table
    op.create_table(
        'ab_tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('experiment_type', sa.String(length=50), nullable=True, comment='page/component/element'),
        sa.Column('target_url', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='draft', comment='draft/running/paused/completed'),
        sa.Column('variants_config', sa.JSON(), nullable=False, comment='Variant configuration'),
        sa.Column('traffic_percentage', sa.Float(), nullable=True, default=100.0),
        sa.Column('primary_metric', sa.String(length=100), nullable=True, comment='conversion/click_through/time_on_page'),
        sa.Column('secondary_metrics', sa.JSON(), nullable=True, comment='Secondary metrics list'),
        sa.Column('min_sample_size', sa.Integer(), nullable=True, default=1000),
        sa.Column('confidence_level', sa.Float(), nullable=True, default=0.95),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('total_visitors', sa.Integer(), nullable=True, default=0),
        sa.Column('winner_variant', sa.String(length=50), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_tests_id'), 'ab_tests', ['id'], unique=False)

    # Create ABTestVariant table
    op.create_table(
        'ab_test_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_config', sa.JSON(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True, default=50.0),
        sa.Column('visitors', sa.Integer(), nullable=True, default=0),
        sa.Column('conversions', sa.Integer(), nullable=True, default=0),
        sa.Column('conversion_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('metrics_data', sa.JSON(), nullable=True),
        sa.Column('is_control', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_tests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_variants_id'), 'ab_test_variants', ['id'], unique=False)

    # Create ABTestEvent table
    op.create_table(
        'ab_test_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('variant_id', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False, comment='impression/click/conversion/scroll'),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True, comment='desktop/mobile/tablet'),
        sa.Column('browser', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_tests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_events_id'), 'ab_test_events', ['id'], unique=False)
    op.create_index(op.f('ix_ab_test_events_session_id'), 'ab_test_events', ['session_id'], unique=False)
    op.create_index(op.f('ix_ab_test_events_created_at'), 'ab_test_events', ['created_at'], unique=False)

    # Create ABTestConversion table
    op.create_table(
        'ab_test_conversions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.String(length=50), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('conversion_type', sa.String(length=50), nullable=False, comment='form_submit/click/purchase'),
        sa.Column('conversion_value', sa.Float(), nullable=True, default=0.0),
        sa.Column('conversion_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_tests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_conversions_id'), 'ab_test_conversions', ['id'], unique=False)
    op.create_index(op.f('ix_ab_test_conversions_session_id'), 'ab_test_conversions', ['session_id'], unique=False)
    op.create_index(op.f('ix_ab_test_conversions_created_at'), 'ab_test_conversions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('ab_test_conversions')
    op.drop_table('ab_test_events')
    op.drop_table('ab_test_variants')
    op.drop_table('ab_tests')
