"""add missing composite indexes for query performance

Revision ID: 057_add_missing_indexes
Revises: 056_merge_055_heads
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "057_add_missing_indexes"
down_revision = "056_merge_055_heads"
branch_labels = None
depends_on = None

_INDEX_DEFS = [
    ("inquiries", "ix_inquiries_tenant_status", ["tenant_id", "status"]),
    ("orders", "ix_orders_merchant_status", ["merchant_id", "status"]),
    ("content_pages", "ix_content_pages_type_status", ["page_type", "status"]),
    ("publish_tasks", "ix_publish_tasks_tenant_status", ["tenant_id", "status"]),
    ("notifications", "ix_notifications_user_read", ["user_id", "is_read"]),
    ("reviews", "ix_reviews_product_status", ["product_id", "status"]),
    (
        "keyword_rankings",
        "ix_keyword_rankings_engine_keyword",
        ["search_engine", "keyword"],
    ),
    ("chat_messages", "ix_chat_messages_session_role", ["session_id", "role"]),
    (
        "international_inquiries",
        "ix_intl_inquiries_status_region",
        ["status", "region"],
    ),
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table, index_name, columns in _INDEX_DEFS:
        # skip if the table does not exist (migration may run on partial schemas)
        if table not in inspector.get_table_names():
            continue
        # 2026-09-05 P0-B：列也须存在——清单含引用 102 才补的 tenant_id 的复合索引，
        # 绿色链 057 << 102，无守卫则 UndefinedColumn
        cols = {c["name"] for c in inspector.get_columns(table)}
        if not set(columns) <= cols:
            continue
        existing = {idx["name"] for idx in inspector.get_indexes(table)}
        if index_name not in existing:
            op.create_index(index_name, table, columns)


def downgrade() -> None:
    for table, index_name, _columns in reversed(_INDEX_DEFS):
        op.drop_index(index_name, table_name=table)
