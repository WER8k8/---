"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "001_initial_schema"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_id_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    ID_TYPE = get_id_type()

    op.create_table(
        "categories",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, index=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text()),
        sa.Column("parent_id", ID_TYPE, nullable=True),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
    )

    op.create_table(
        "content_pages",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False, index=True),
        sa.Column("content", sa.Text()),
        sa.Column("summary", sa.String(500)),
        sa.Column("page_type", sa.String(50), index=True, default="page"),
        sa.Column("status", sa.String(20), nullable=False, default="draft"),
        sa.Column("author_id", ID_TYPE, nullable=True, index=True),
        sa.Column("view_count", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "inquiries",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("product", sa.String(100)),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "keywords",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("keyword", sa.String(200), nullable=False, index=True),
        sa.Column("slug", sa.String(200), nullable=False, index=True),
        sa.Column("search_volume", sa.Integer(), default=0),
        sa.Column("difficulty", sa.String(20), default="medium"),
        sa.Column("current_ranking", sa.Integer(), nullable=True),
        sa.Column("target_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "keyword_rankings",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("keyword_id", ID_TYPE, nullable=False, index=True),
        sa.Column("ranking", sa.Integer()),
        sa.Column("page_url", sa.String(500)),
        sa.Column("search_engine", sa.String(50), default="baidu"),
        sa.Column("checked_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "llms_config",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("section", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("version", sa.String(20), default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "operation_logs",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("user_id", ID_TYPE, nullable=True, index=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(50)),
        sa.Column("detail", sa.Text()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "products",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("category_id", ID_TYPE, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False, index=True),
        sa.Column("subtitle", sa.String(300)),
        sa.Column("description", sa.Text()),
        sa.Column("technical_params", sa.Text()),
        sa.Column("application_scenarios", sa.Text()),
        sa.Column("advantages", sa.Text()),
        sa.Column("specifications", sa.Text()),
        sa.Column("density", sa.String(50)),
        sa.Column("strength", sa.String(50)),
        sa.Column("thermal_conductivity", sa.String(50)),
        sa.Column("unit_weight", sa.String(50)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("meta_title", sa.String(200)),
        sa.Column("meta_description", sa.String(500)),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("view_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
    )

    op.create_table(
        "seo_metadata",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("resource_type", sa.String(50), nullable=False, index=True),
        sa.Column("resource_id", sa.String(50), nullable=False, index=True),
        sa.Column("meta_title", sa.String(200)),
        sa.Column("meta_description", sa.String(500)),
        sa.Column("meta_keywords", sa.String(300)),
        sa.Column("canonical_url", sa.String(500)),
        sa.Column("og_title", sa.String(200)),
        sa.Column("og_description", sa.String(500)),
        sa.Column("og_image", sa.String(500)),
        sa.Column("schema_markup", sa.Text()),
        sa.Column("noindex", sa.Boolean(), default=False),
        sa.Column("h1_tag", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "site_audits",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("url", sa.String(500)),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("audit_type", sa.String(50), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("total_issues", sa.Integer(), default=0),
        sa.Column("critical_issues", sa.Integer(), default=0),
        sa.Column("warning_issues", sa.Integer(), default=0),
        sa.Column("report_data", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ai_optimization_logs",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(50), nullable=False),
        sa.Column("optimization_type", sa.String(50), nullable=False),
        sa.Column("original_content", sa.Text()),
        sa.Column("optimized_content", sa.Text()),
        sa.Column("model_used", sa.String(100)),
        sa.Column("tokens_used", sa.Integer(), default=0),
        sa.Column("score_before", sa.Float()),
        sa.Column("score_after", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "users",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("role", sa.String(20), nullable=False, default="viewer"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("ai_optimization_logs")
    op.drop_table("site_audits")
    op.drop_table("seo_metadata")
    op.drop_table("products")
    op.drop_table("operation_logs")
    op.drop_table("llms_config")
    op.drop_table("keyword_rankings")
    op.drop_table("keywords")
    op.drop_table("inquiries")
    op.drop_table("content_pages")
    op.drop_table("categories")
