"""add case_studies and case_images tables

Revision ID: 003
Revises: 002
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_add_case_studies"
down_revision: Union[str, None] = "002_add_product_documents"

def get_id_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)
    return sa.String(36)

def upgrade() -> None:
    ID_TYPE = get_id_type()
    op.create_table(
        "case_studies",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("client_name", sa.String(255)),
        sa.Column("materials_used", sa.String(500)),
        sa.Column("construction_area", sa.String(100)),
        sa.Column("project_date", sa.String(50)),
        sa.Column("location", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("cover_image", sa.String(500)),
        sa.Column("status", sa.String(20), default="draft"),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("view_count", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "case_images",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("case_id", ID_TYPE, nullable=False, index=True),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("image_alt", sa.String(255)),
        sa.Column("sort_order", sa.Integer, default=0),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["case_id"], ["case_studies.id"], ondelete="CASCADE"),
    )

def downgrade() -> None:
    op.drop_table("case_images")
    op.drop_table("case_studies")
