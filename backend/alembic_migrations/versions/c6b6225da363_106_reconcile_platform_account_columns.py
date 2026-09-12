"""106: reconcile platform account columns for the unified model.

The model layer now owns platform account binding fields, but the first
PostgreSQL migration created the table with a narrower shape. This migration
adds only missing nullable columns and leaves legacy credential columns intact.

Revision ID: c6b6225da363
Revises: 105_reconcile_model_backfill
Create Date: 2026-09-10
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6b6225da363"
down_revision: Union[str, None] = "105_reconcile_model_backfill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'platform_accounts'"
        ))
    }
    columns = {
        "username": sa.Column("username", sa.String(100), nullable=True),
        "email": sa.Column("email", sa.String(100), nullable=True),
        "cookie_data": sa.Column("cookie_data", sa.Text(), nullable=True),
        "token_data": sa.Column("token_data", sa.JSON(), nullable=True),
        "token_expire_at": sa.Column("token_expire_at", sa.DateTime(timezone=True), nullable=True),
        "login_status": sa.Column("login_status", sa.String(20), nullable=True),
        "last_login_at": sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    }
    for name, column in columns.items():
        if name not in existing:
            op.add_column("platform_accounts", column)


def downgrade() -> None:
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'platform_accounts'"
        ))
    }
    for name in ("last_login_at", "login_status", "token_expire_at", "token_data", "cookie_data", "email", "username"):
        if name in existing:
            op.drop_column("platform_accounts", name)
