"""Alembic配置 - 数据库迁移管理"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context
# 导入所有模型
from app.core.config import settings
from app.core.database import Base
from app.models.ab_test import (ABTest, ABTestConversion, ABTestEvent,
                                ABTestVariant)
from app.models.case_study import CaseImage, CaseStudy
from app.models.compliance import (AdvertisementLawKeyword, ComplianceRule,
                                   ComplianceScanResult, ComplianceViolation)
from app.models.content import ContentPage, ContentVersion
# 2026-09-05：SeoMetadata 已被并行重构迁至 seo_metadata.py（原从 content 导入，
# content.py 18:22 重构后不再 re-export，绿色链 env 加载即 ImportError）
from app.models.seo_metadata import SeoMetadata
from app.models.eeat import (ArticleAuthor, Author, AuthorCertification,
                             EEATScore, TrustSignal)
from app.models.feishu import FeishuBinding, FeishuMessageLog
from app.models.inquiry import Inquiry
from app.models.payment import PaymentChannel, PaymentOrder
from app.models.product import Category, Product, ProductDocument
from app.models.schema_markup import SchemaMarkup, SchemaTemplate
from app.models.seo import (AiOptimizationLog, Keyword, KeywordRanking,
                            LlmsConfig, SiteAudit)
from app.models.user import OperationLog, User

# Alembic配置对象
config = context.config

# 设置日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
target_metadata = Base.metadata


# 从环境变量获取数据库URL
def get_url():
    return os.getenv("DATABASE_URL", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _widen_alembic_version_column(connection) -> None:
    if connection.dialect.name != "postgresql":
        return
    connection.execute(
        text(
            """
            DO $$ BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'alembic_version'
              ) THEN
                ALTER TABLE alembic_version
                ALTER COLUMN version_num TYPE VARCHAR(128);
              END IF;
            END $$;
            """
        )
    )


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            _widen_alembic_version_column(connection)
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
