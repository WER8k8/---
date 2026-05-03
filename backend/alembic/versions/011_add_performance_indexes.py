"""add performance indexes

Revision ID: 011_add_performance_indexes
Revises: 010_add_ab_test_tables
Create Date: 2026-05-03 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '011_add_performance_indexes'
down_revision = '010_add_ab_test_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)
    op.create_index('ix_products_category_id', 'products', ['category_id'])
    op.create_index('ix_products_is_active', 'products', ['is_active'])
    op.create_index('ix_products_created_at', 'products', ['created_at'])
    op.create_index('ix_products_updated_at', 'products', ['updated_at'])

    op.create_index('ix_case_studies_slug', 'case_studies', ['slug'], unique=True)
    op.create_index('ix_case_studies_is_published', 'case_studies', ['is_published'])
    op.create_index('ix_case_studies_created_at', 'case_studies', ['created_at'])

    op.create_index('ix_content_pages_slug', 'content_pages', ['slug'], unique=True)
    op.create_index('ix_content_pages_type', 'content_pages', ['type'])
    op.create_index('ix_content_pages_is_published', 'content_pages', ['is_published'])
    op.create_index('ix_content_pages_created_at', 'content_pages', ['created_at'])

    op.create_index('ix_inquiries_status', 'inquiries', ['status'])
    op.create_index('ix_inquiries_created_at', 'inquiries', ['created_at'])
    op.create_index('ix_inquiries_email', 'inquiries', ['email'])

    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    op.create_index('ix_seo_analyses_url', 'seo_analyses', ['url'])
    op.create_index('ix_seo_analyses_created_at', 'seo_analyses', ['created_at'])
    op.create_index('ix_seo_analyses_score', 'seo_analyses', ['score'])

    op.create_index('ix_schema_markups_url', 'schema_markups', ['url'])
    op.create_index('ix_schema_markups_schema_type', 'schema_markups', ['schema_type'])

    op.create_index('ix_eeat_signals_url', 'eeat_signals', ['url'])
    op.create_index('ix_eeat_signals_score', 'eeat_signals', ['score'])

    op.create_index('ix_compliance_reports_url', 'compliance_reports', ['url'])
    op.create_index('ix_compliance_reports_status', 'compliance_reports', ['status'])

    op.create_index('ix_keyword_rankings_keyword', 'keyword_rankings', ['keyword'])
    op.create_index('ix_keyword_rankings_position', 'keyword_rankings', ['position'])
    op.create_index('ix_keyword_rankings_tracked_at', 'keyword_rankings', ['tracked_at'])

    op.create_index('ix_ab_tests_status', 'ab_tests', ['status'])
    op.create_index('ix_ab_tests_created_at', 'ab_tests', ['created_at'])
    op.create_index('ix_ab_test_variants_experiment_id', 'ab_test_variants', ['experiment_id'])
    op.create_index('ix_ab_test_events_experiment_id', 'ab_test_events', ['experiment_id'])
    op.create_index('ix_ab_test_events_event_type', 'ab_test_events', ['event_type'])
    op.create_index('ix_ab_test_conversions_experiment_id', 'ab_test_conversions', ['experiment_id'])


def downgrade() -> None:
    op.drop_index('ix_products_slug', table_name='products')
    op.drop_index('ix_products_category_id', table_name='products')
    op.drop_index('ix_products_is_active', table_name='products')
    op.drop_index('ix_products_created_at', table_name='products')
    op.drop_index('ix_products_updated_at', table_name='products')

    op.drop_index('ix_case_studies_slug', table_name='case_studies')
    op.drop_index('ix_case_studies_is_published', table_name='case_studies')
    op.drop_index('ix_case_studies_created_at', table_name='case_studies')

    op.drop_index('ix_content_pages_slug', table_name='content_pages')
    op.drop_index('ix_content_pages_type', table_name='content_pages')
    op.drop_index('ix_content_pages_is_published', table_name='content_pages')
    op.drop_index('ix_content_pages_created_at', table_name='content_pages')

    op.drop_index('ix_inquiries_status', table_name='inquiries')
    op.drop_index('ix_inquiries_created_at', table_name='inquiries')
    op.drop_index('ix_inquiries_email', table_name='inquiries')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_is_active', table_name='users')

    op.drop_index('ix_seo_analyses_url', table_name='seo_analyses')
    op.drop_index('ix_seo_analyses_created_at', table_name='seo_analyses')
    op.drop_index('ix_seo_analyses_score', table_name='seo_analyses')

    op.drop_index('ix_schema_markups_url', table_name='schema_markups')
    op.drop_index('ix_schema_markups_schema_type', table_name='schema_markups')

    op.drop_index('ix_eeat_signals_url', table_name='eeat_signals')
    op.drop_index('ix_eeat_signals_score', table_name='eeat_signals')

    op.drop_index('ix_compliance_reports_url', table_name='compliance_reports')
    op.drop_index('ix_compliance_reports_status', table_name='compliance_reports')

    op.drop_index('ix_keyword_rankings_keyword', table_name='keyword_rankings')
    op.drop_index('ix_keyword_rankings_position', table_name='keyword_rankings')
    op.drop_index('ix_keyword_rankings_tracked_at', table_name='keyword_rankings')

    op.drop_index('ix_ab_tests_status', table_name='ab_tests')
    op.drop_index('ix_ab_tests_created_at', table_name='ab_tests')
    op.drop_index('ix_ab_test_variants_experiment_id', table_name='ab_test_variants')
    op.drop_index('ix_ab_test_events_experiment_id', table_name='ab_test_events')
    op.drop_index('ix_ab_test_events_event_type', table_name='ab_test_events')
    op.drop_index('ix_ab_test_conversions_experiment_id', table_name='ab_test_conversions')
