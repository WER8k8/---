"""补齐剩余 3 张表的缺列"""
import os
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault("ENV_FILE", "config/dev/.env")
os.environ.setdefault("PYTHONPATH", ".")
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

# 从模型读出声明的列类型
def col_type_map(table_name):
    t = Base.metadata.tables[table_name]
    out = {}
    for c in t.columns:
        out[c.name] = c.type.compile(engine.dialect)
    return out

additions = []
for table_name, table in Base.metadata.tables.items():
    try:
        actual_cols = {c["name"] for c in inspector.get_columns(table_name)}
    except Exception:
        continue
    for col_name, col_type in col_type_map(table_name).items():
        if col_name not in actual_cols:
            additions.append((table_name, col_name, col_type))

logger.info('待添加列: {len(additions)}', len(additions))
with engine.begin() as conn:
    for t, c, ty in additions:
        sql = f'ALTER TABLE {t} ADD COLUMN "{c}" {ty}'
        try:
            conn.execute(text(sql))
            logger.info('  ✅ {t}.{c} {ty}', t, c, ty)
        except Exception as e:
            logger.info('  ❌ {t}.{c} -> {e}', t, c, e)

# 再核
logger.info("\n=== 复检 ===")
inspector = inspect(engine)
still_missing = 0
for table_name, table in Base.metadata.tables.items():
    try:
        actual_cols = {c["name"] for c in inspector.get_columns(table_name)}
    except Exception:
        continue
    model_cols = {c.name for c in table.columns}
    missing = model_cols - actual_cols
    if missing:
        still_missing += len(missing)
        logger.info('  ❌ {table_name}: 缺列 {sorted(missing)}', table_name, sorted(missing))
logger.info(f"剩余缺列: {still_missing}")
