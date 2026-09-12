"""创建商家IM路由配置表和建材垂直参数表

Revision ID: 021
Revises: 020 (pgvector扩展)
Create Date: 2026-05-23

根据文档14.1章节，创建两个核心表：
1. merchant_im_routing - 商家即时通讯分流配置表
2. building_material_specs - 建材垂直参数表
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '021_create_im_routing_and_specs'
down_revision = '020_add_pgvector'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    # === 表一：商家即时通讯分流配置表 `merchant_im_routing` ===
    if "merchant_im_routing" not in existing:
        op.create_table(
            'merchant_im_routing',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('merchant_id', sa.Integer(), nullable=False),
            sa.Column('country_code', sa.String(2), nullable=False),
            sa.Column('channel_type', sa.String(20), nullable=False),
            sa.Column('account_id', sa.String(100), nullable=False),
            sa.Column('prefilled_text', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        )
        op.create_index(
            'idx_merchant_country',
            'merchant_im_routing',
            ['merchant_id', 'country_code'],
            unique=False,
        )

    # === 表二：建材垂直参数表 `building_material_specs` ===
    if "building_material_specs" not in existing:
        trust_badges_type = sa.JSON() if bind.dialect.name == "sqlite" else sa.ARRAY(sa.String(50))
        op.create_table(
            'building_material_specs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('spec_key', sa.String(50), nullable=False),
            sa.Column('spec_value', sa.Numeric(), nullable=False),
            sa.Column('metric_unit', sa.String(10), nullable=False),
            sa.Column('imperial_unit', sa.String(10), nullable=True),
            sa.Column('imperial_scale_factor', sa.Numeric(), nullable=True),
            sa.Column('trust_badges', trust_badges_type, nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        )
        op.create_index(
            'idx_product_spec',
            'building_material_specs',
            ['product_id', 'spec_key'],
            unique=False,
        )


def downgrade() -> None:
    # 删除表（降级）
    op.drop_table('building_material_specs')
    op.drop_table('merchant_im_routing')
