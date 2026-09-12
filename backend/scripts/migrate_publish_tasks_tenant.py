"""一次性迁移:补齐 publish_tasks.tenant_id 列"""
import os
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("ENV_FILE", "config/dev/.env")
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    rows = conn.execute(text("PRAGMA table_info('publish_tasks')")).fetchall()
    logger.info('publish_tasks 当前列:')
    for r in rows:
        logger.info('" ", r[1], r[2]')
    has_tenant = any(r[1] == "tenant_id" for r in rows)
    logger.info('"has tenant_id:", has_tenant')
    if not has_tenant:
        logger.info('>>> 添加 tenant_id 列')
        conn.execute(text("ALTER TABLE publish_tasks ADD COLUMN tenant_id VARCHAR(36)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_publish_tasks_tenant_id ON publish_tasks(tenant_id)"))
        conn.commit()
        logger.info('✅ tenant_id 已添加')

    # 补齐 UTM 4 列
    for col, typedef in [
        ("utm_source", "VARCHAR(120)"),
        ("utm_medium", "VARCHAR(120)"),
        ("utm_campaign", "VARCHAR(200)"),
        ("utm_content", "VARCHAR(200)"),
    ]:
        if not any(r[1] == col for r in rows):
            logger.info('>>> 添加 {col}', col)
            conn.execute(text(f"ALTER TABLE publish_tasks ADD COLUMN {col} {typedef}"))
            conn.commit()
            logger.info('✅ {col} 已添加', col)
    conn.commit()
    logger.info('完成')
    # 重新读
    rows2 = conn.execute(text("PRAGMA table_info('publish_tasks')")).fetchall()
    logger.info('"最终列数:", len(rows2)')
