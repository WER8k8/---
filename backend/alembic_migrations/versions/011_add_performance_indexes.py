"""add performance indexes

Revision ID: 011_add_performance_indexes
Revises: 010_add_ab_test_tables
Create Date: 2026-05-03 10:00:00.000000

"""

from sqlalchemy.exc import OperationalError, ProgrammingError

from alembic import op

# revision identifiers, used by Alembic.
revision = "011_add_performance_indexes"
down_revision = "010_add_ab_test_tables"
branch_labels = None
depends_on = None


def create_index_safe(index_name, table_name, columns, unique=False):
    try:
        with op.get_context().autocommit_block():
            op.create_index(index_name, table_name, columns, unique=unique)
    except (OperationalError, ProgrammingError):
        pass


def upgrade() -> None:
    create_index_safe("ix_products_slug", "products", ["slug"], unique=True)
    create_index_safe("ix_products_category_id", "products", ["category_id"])
    create_index_safe("ix_products_is_active", "products", ["is_active"])
    create_index_safe("ix_products_created_at", "products", ["created_at"])
    create_index_safe("ix_products_updated_at", "products", ["updated_at"])

    create_index_safe(
        "ix_case_studies_slug",
        "case_studies",
        ["slug"],
        unique=True)
    create_index_safe(
        "ix_case_studies_is_published",
        "case_studies",
        ["is_published"])
    create_index_safe(
        "ix_case_studies_created_at",
        "case_studies",
        ["created_at"])

    create_index_safe(
        "ix_content_pages_slug",
        "content_pages",
        ["slug"],
        unique=True)
    create_index_safe("ix_content_pages_type", "content_pages", ["type"])
    create_index_safe(
        "ix_content_pages_is_published",
        "content_pages",
        ["is_published"])
    create_index_safe(
        "ix_content_pages_created_at",
        "content_pages",
        ["created_at"])

    create_index_safe("ix_inquiries_status", "inquiries", ["status"])
    create_index_safe("ix_inquiries_created_at", "inquiries", ["created_at"])
    create_index_safe("ix_inquiries_email", "inquiries", ["email"])

    create_index_safe("ix_users_email", "users", ["email"], unique=True)
    create_index_safe("ix_users_username", "users", ["username"], unique=True)
    create_index_safe("ix_users_role", "users", ["role"])
    create_index_safe("ix_users_is_active", "users", ["is_active"])

    create_index_safe("ix_seo_analyses_url", "seo_analyses", ["url"])
    create_index_safe(
        "ix_seo_analyses_created_at",
        "seo_analyses",
        ["created_at"])
    create_index_safe("ix_seo_analyses_score", "seo_analyses", ["score"])

    create_index_safe("ix_schema_markups_url", "schema_markups", ["url"])
    create_index_safe(
        "ix_schema_markups_schema_type",
        "schema_markups",
        ["schema_type"])

    create_index_safe("ix_eeat_signals_url", "eeat_signals", ["url"])
    create_index_safe("ix_eeat_signals_score", "eeat_signals", ["score"])

    create_index_safe(
        "ix_compliance_reports_url",
        "compliance_reports",
        ["url"])
    create_index_safe(
        "ix_compliance_reports_status",
        "compliance_reports",
        ["status"])

    create_index_safe(
        "ix_keyword_rankings_keyword",
        "keyword_rankings",
        ["keyword"])
    create_index_safe(
        "ix_keyword_rankings_position",
        "keyword_rankings",
        ["position"])
    create_index_safe(
        "ix_keyword_rankings_tracked_at",
        "keyword_rankings",
        ["tracked_at"])

    create_index_safe("ix_ab_tests_status", "ab_tests", ["status"])
    create_index_safe("ix_ab_tests_created_at", "ab_tests", ["created_at"])
    create_index_safe(
        "ix_ab_test_variants_experiment_id",
        "ab_test_variants",
        ["experiment_id"])
    create_index_safe(
        "ix_ab_test_events_experiment_id",
        "ab_test_events",
        ["experiment_id"])
    create_index_safe(
        "ix_ab_test_events_event_type",
        "ab_test_events",
        ["event_type"])
    create_index_safe(
        "ix_ab_test_conversions_experiment_id",
        "ab_test_conversions",
        ["experiment_id"])


def downgrade() -> None:
    op.drop_index("ix_products_slug", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_index("ix_products_is_active", table_name="products")
    op.drop_index("ix_products_created_at", table_name="products")
    op.drop_index("ix_products_updated_at", table_name="products")

    op.drop_index("ix_case_studies_slug", table_name="case_studies")
    op.drop_index("ix_case_studies_is_published", table_name="case_studies")
    op.drop_index("ix_case_studies_created_at", table_name="case_studies")

    op.drop_index("ix_content_pages_slug", table_name="content_pages")
    op.drop_index("ix_content_pages_type", table_name="content_pages")
    op.drop_index("ix_content_pages_is_published", table_name="content_pages")
    op.drop_index("ix_content_pages_created_at", table_name="content_pages")

    op.drop_index("ix_inquiries_status", table_name="inquiries")
    op.drop_index("ix_inquiries_created_at", table_name="inquiries")
    op.drop_index("ix_inquiries_email", table_name="inquiries")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_is_active", table_name="users")

    op.drop_index("ix_seo_analyses_url", table_name="seo_analyses")
    op.drop_index("ix_seo_analyses_created_at", table_name="seo_analyses")
    op.drop_index("ix_seo_analyses_score", table_name="seo_analyses")

    op.drop_index("ix_schema_markups_url", table_name="schema_markups")
    op.drop_index("ix_schema_markups_schema_type", table_name="schema_markups")

    op.drop_index("ix_eeat_signals_url", table_name="eeat_signals")
    op.drop_index("ix_eeat_signals_score", table_name="eeat_signals")

    op.drop_index("ix_compliance_reports_url", table_name="compliance_reports")
    op.drop_index(
        "ix_compliance_reports_status",
        table_name="compliance_reports")

    op.drop_index("ix_keyword_rankings_keyword", table_name="keyword_rankings")
    op.drop_index(
        "ix_keyword_rankings_position",
        table_name="keyword_rankings")
    op.drop_index(
        "ix_keyword_rankings_tracked_at",
        table_name="keyword_rankings")

    op.drop_index("ix_ab_tests_status", table_name="ab_tests")
    op.drop_index("ix_ab_tests_created_at", table_name="ab_tests")
    op.drop_index(
        "ix_ab_test_variants_experiment_id",
        table_name="ab_test_variants")
    op.drop_index(
        "ix_ab_test_events_experiment_id",
        table_name="ab_test_events")
    op.drop_index("ix_ab_test_events_event_type", table_name="ab_test_events")
    op.drop_index(
        "ix_ab_test_conversions_experiment_id",
        table_name="ab_test_conversions")
