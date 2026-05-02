"""add product_documents table and fire_rating field

Revision ID: 002
Revises: 001
Create Date: 2026-05-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_add_product_documents"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_id_type():
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)
    return sa.String(36)


def upgrade() -> None:
    ID_TYPE = get_id_type()

    op.add_column("products", sa.Column("fire_rating", sa.String(20)))

    op.create_table(
        "product_documents",
        sa.Column("id", ID_TYPE, primary_key=True),
        sa.Column("product_id", ID_TYPE, nullable=False, index=True),
        sa.Column("doc_type", sa.String(20), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), default=0),
        sa.Column("description", sa.String(500)),
        sa.Column("sort_order", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )


def downgrade() -> None:
    op.drop_table("product_documents")
    op.drop_column("products", "fire_rating")
