"""Add missing tables for B2B foreign trade platform

Revision ID: 022_add_missing_tables
Revises: 021_create_im_routing_and_specs
Create Date: 2026-05-23

Tables added:
- merchant_profiles (商家资料)
- inquiries (询盘)
- quotes (报价)
- orders (订单)
- order_items (订单明细)
- product_categories (产品分类)
- product_images (产品图片)
- content_pages (内容页面)
- seo_metadata (SEO元数据)
- ai_recommendations (AI推荐)
- chat_sessions (AI对话会话)
- chat_messages (AI对话消息)
- system_config (系统配置)
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# revision identifiers, used by Alembic.
revision = '022_add_missing_tables'
down_revision = '021_create_im_routing_and_specs'
branch_labels = None
depends_on = None


def _existing_tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def create_table_if_absent(table_name, *args, **kwargs):
    if table_name in _existing_tables():
        return
    op.create_table(table_name, *args, **kwargs)


def create_index_if_absent(index_name, table_name, columns, **kwargs):
    if table_name not in _existing_tables():
        return
    try:
        with op.get_context().autocommit_block():
            op.create_index(index_name, table_name, columns, **kwargs)
    except Exception:
        pass


def upgrade() -> None:
    # 1. merchant_profiles (商家资料)
    create_table_if_absent(
        'merchant_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('company_address', sa.Text, nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('business_license', sa.String(255), nullable=True),  # 营业执照
        sa.Column('verified', sa.Boolean, default=False),  # 是否认证
        sa.Column('verification_documents', JSONB, nullable=True),  # 认证文档URLs
        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('whatsapp_number', sa.String(50), nullable=True),
        sa.Column('wechat_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_merchant_profiles_user_id', 'merchant_profiles', ['user_id'])
    create_index_if_absent('idx_merchant_profiles_verified', 'merchant_profiles', ['verified'])

    # 2. product_categories (产品分类)
    create_table_if_absent(
        'product_categories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),  # 分类名称（多语言用JSON）
        sa.Column('name_i18n', JSONB, nullable=True),  # 多语言名称 {"en": "Tiles", "zh": "瓷砖"}
        sa.Column('slug', sa.String(255), nullable=False, unique=True),  # URL slug
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('product_categories.id'), nullable=True),  # 父分类
        sa.Column('level', sa.Integer, default=0),  # 层级（0=一级，1=二级...）
        sa.Column('icon_url', sa.String(500), nullable=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_product_categories_slug', 'product_categories', ['slug'])
    create_index_if_absent('idx_product_categories_parent_id', 'product_categories', ['parent_id'])

    # 3. product_images (产品图片)
    create_table_if_absent(
        'product_images',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('alt_text', sa.String(255), nullable=True),  # 图片alt（SEO）
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('is_primary', sa.Boolean, default=False),  # 是否主图
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    create_index_if_absent('idx_product_images_product_id', 'product_images', ['product_id'])

    # 4. inquiries (询盘)
    create_table_if_absent(
        'inquiries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('buyer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),  # 买家
        sa.Column('merchant_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),  # 商家
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=True),  # 关联产品
        sa.Column('subject', sa.String(255), nullable=False),  # 询盘主题
        sa.Column('message', sa.Text, nullable=False),  # 询盘内容
        sa.Column('quantity', sa.Integer, nullable=True),  # 数量
        sa.Column('unit', sa.String(50), nullable=True),  # 单位（平米、吨等）
        sa.Column('target_price_min', sa.Numeric(10, 2), nullable=True),  # 目标价格下限
        sa.Column('target_price_max', sa.Numeric(10, 2), nullable=True),  # 目标价格上限
        sa.Column('currency', sa.String(10), default='USD'),
        sa.Column('delivery_date', sa.Date, nullable=True),  # 期望交货日期
        sa.Column('status', sa.String(50), default='pending'),  # pending/quoted/accepted/rejected
        # 2026-09-05 P0-B：补 assigned_to/source_channel（模型在列，036/027 依赖；
        # 迁移版建表缺列曾致绿色链 036 建 index 崩 UndefinedColumn）
        sa.Column('assigned_to', sa.String(36), nullable=True),  # 平台线索 CRM 指派
        sa.Column('source_channel', sa.String(50), nullable=True),  # 询盘来源渠道
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_inquiries_buyer_id', 'inquiries', ['buyer_id'])
    create_index_if_absent('idx_inquiries_merchant_id', 'inquiries', ['merchant_id'])
    create_index_if_absent('idx_inquiries_status', 'inquiries', ['status'])

    # 5. quotes (报价)
    create_table_if_absent(
        'quotes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('inquiry_id', UUID(as_uuid=True), sa.ForeignKey('inquiries.id'), nullable=False),
        sa.Column('merchant_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), default='USD'),
        sa.Column('valid_until', sa.Date, nullable=True),  # 报价有效期
        sa.Column('payment_terms', sa.Text, nullable=True),  # 付款条款
        sa.Column('delivery_terms', sa.Text, nullable=True),  # 交货条款
        sa.Column('status', sa.String(50), default='draft'),  # draft/sent/accepted/expired
        sa.Column('pdf_url', sa.String(500), nullable=True),  # 报价单PDF
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_quotes_inquiry_id', 'quotes', ['inquiry_id'])
    create_index_if_absent('idx_quotes_merchant_id', 'quotes', ['merchant_id'])

    # 6. orders (订单)
    create_table_if_absent(
        'orders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('buyer_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('merchant_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('quote_id', UUID(as_uuid=True), sa.ForeignKey('quotes.id'), nullable=True),
        sa.Column('order_number', sa.String(100), nullable=False, unique=True),  # 订单号
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(10), default='USD'),
        sa.Column('status', sa.String(50), default='pending'),  # pending/confirmed/shipped/completed/cancelled
        sa.Column('payment_status', sa.String(50), default='unpaid'),  # unpaid/partial/paid/refunded
        sa.Column('shipping_address', sa.Text, nullable=True),
        sa.Column('shipping_method', sa.String(100), nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('estimated_delivery', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_orders_buyer_id', 'orders', ['buyer_id'])
    create_index_if_absent('idx_orders_merchant_id', 'orders', ['merchant_id'])
    create_index_if_absent('idx_orders_status', 'orders', ['status'])

    # 7. order_items (订单明细)
    create_table_if_absent(
        'order_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('order_id', UUID(as_uuid=True), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('specifications', JSONB, nullable=True),  # 选购的规格
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    create_index_if_absent('idx_order_items_order_id', 'order_items', ['order_id'])

    # 8. content_pages (内容页面)
    create_table_if_absent(
        'content_pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('content', sa.Text, nullable=False),  # HTML内容
        sa.Column('content_type', sa.String(50), default='blog'),  # blog/guide/case_study/news
        sa.Column('author_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('status', sa.String(50), default='draft'),  # draft/published/archived
        sa.Column('published_at', sa.DateTime, nullable=True),
        sa.Column('featured_image', sa.String(500), nullable=True),
        sa.Column('reading_time', sa.Integer, nullable=True),  # 预估阅读时间（分钟）
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('language', sa.String(10), default='en'),  # 语言
        sa.Column('hreflang_group', UUID(as_uuid=True), nullable=True),  # 多语言关联组
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_content_pages_slug', 'content_pages', ['slug'])
    create_index_if_absent('idx_content_pages_status', 'content_pages', ['status'])
    create_index_if_absent('idx_content_pages_language', 'content_pages', ['language'])

    # 9. seo_metadata (SEO元数据)
    create_table_if_absent(
        'seo_metadata',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('entity_type', sa.String(50), nullable=False),  # product/content/page
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.Text, nullable=True),
        sa.Column('meta_keywords', sa.String(500), nullable=True),
        sa.Column('og_title', sa.String(255), nullable=True),
        sa.Column('og_description', sa.Text, nullable=True),
        sa.Column('og_image', sa.String(500), nullable=True),
        sa.Column('canonical_url', sa.String(500), nullable=True),
        sa.Column('hreflang_tags', JSONB, nullable=True),  # [{"lang": "en", "url": "..."}]
        sa.Column('structured_data', JSONB, nullable=True),  # Schema.org JSON-LD
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_seo_metadata_entity', 'seo_metadata', ['entity_type', 'entity_id'])

    # 10. ai_recommendations (AI推荐)
    create_table_if_absent(
        'ai_recommendations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('product_id', UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('score', sa.Numeric(5, 4), nullable=False),  # 推荐分数（0-1）
        sa.Column('reason', sa.Text, nullable=True),  # 推荐理由
        sa.Column('algorithm', sa.String(100), nullable=True),  # 使用的算法
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    create_index_if_absent('idx_ai_recommendations_user_id', 'ai_recommendations', ['user_id'])
    create_index_if_absent('idx_ai_recommendations_product_id', 'ai_recommendations', ['product_id'])

    # 11. chat_sessions (AI对话会话)
    create_table_if_absent(
        'chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('session_name', sa.String(255), nullable=True),  # 会话名称（用户自定义）
        sa.Column('model_used', sa.String(100), nullable=True),  # 使用的模型
        sa.Column('total_tokens', sa.Integer, default=0),
        sa.Column('status', sa.String(50), default='active'),  # active/archived
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])

    # 12. chat_messages (AI对话消息)
    create_table_if_absent(
        'chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),  # user/assistant/system
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('tokens', sa.Integer, nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    create_index_if_absent('idx_chat_messages_session_id', 'chat_messages', ['session_id'])

    # 13. system_config (系统配置)
    create_table_if_absent(
        'system_config',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key', sa.String(255), nullable=False, unique=True),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('value_type', sa.String(50), default='string'),  # string/number/boolean/json
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_public', sa.Boolean, default=False),  # 是否允许前端读取
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    create_index_if_absent('idx_system_config_key', 'system_config', ['key'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('system_config')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('ai_recommendations')
    op.drop_table('seo_metadata')
    op.drop_table('content_pages')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('quotes')
    op.drop_table('inquiries')
    op.drop_table('product_images')
    op.drop_table('product_categories')
    op.drop_table('merchant_profiles')
