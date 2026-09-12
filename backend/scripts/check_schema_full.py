"""全表 schema 完整性检查:对比模型声明的列 vs 实际 DB 列"""
import os
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("ENV_FILE", "config/dev/.env")
os.environ.setdefault("PYTHONPATH", ".")
from sqlalchemy import create_engine, inspect
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401  ensure models imported

engine = create_engine(settings.DATABASE_URL)
db_inspector = inspect(engine)

missing_total = 0
checked = 0
for table_name, table in Base.metadata.tables.items():
    checked += 1
    try:
        actual_cols = {c["name"] for c in db_inspector.get_columns(table_name)}
    except Exception as e:
        logger.info('  ⚠️  {table_name}: 表不存在 ({e})', table_name, e)
        missing_total += 1
        continue
    model_cols = {c.name for c in table.columns}
    missing = model_cols - actual_cols
    if missing:
        missing_total += len(missing)
        logger.info('  ❌ {table_name}: 缺列 {sorted(missing)}', table_name, sorted(missing))

logger.info('\\n检查 {checked} 张表,累计缺列 {missing_total}', checked, missing_total)
