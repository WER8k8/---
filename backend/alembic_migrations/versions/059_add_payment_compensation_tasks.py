"""add payment_compensation_tasks table

Revision ID: 059
Revises: 058
Create Date: 2026-08-29

BUG-02 修复：新增支付权益发放补偿任务表，用于记录支付回调后权益发放失败的情况，
供定时巡检重试直到发放成功。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

def _uuid_col():
    """P0-B canonical：PG=native uuid（对齐模型 UUID_TYPE），其余=String(36)。"""
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(36)


# revision identifiers, used by Alembic.
revision: str = '059'
down_revision: Union[str, None] = '058_merge_all_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_compensation_tasks',
        sa.Column('id', _uuid_col(), nullable=False),
        sa.Column('order_no', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='unknown'),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_payment_compensation_tasks_order_no', 'order_no'),
        sa.Index('ix_payment_compensation_tasks_status', 'status'),
    )


def downgrade() -> None:
    op.drop_index('ix_payment_compensation_tasks_status', table_name='payment_compensation_tasks')
    op.drop_index('ix_payment_compensation_tasks_order_no', table_name='payment_compensation_tasks')
    op.drop_table('payment_compensation_tasks')
