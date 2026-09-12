import warnings
warnings.filterwarnings("ignore")
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    dialect = db.bind.dialect.name
    print("当前数据库方言:", dialect)
    if dialect == "postgresql":
        tables = [r[0] for r in db.execute(text(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'")).fetchall()]
    else:
        tables = [r[0] for r in db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'")).fetchall()]
    print("表数量:", len(tables))
    cand = [t for t in tables if any(k in t.lower() for k in ("admin", "user"))]
    print("账号相关表:", cand)
    for t in cand:
        try:
            n = db.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            print(f"  {t}: {n} 行")
            if n and n < 20:
                cols = [c[0] for c in db.execute(text(
                    f'SELECT column_name FROM information_schema.columns WHERE table_name=:t'), {"t": t}).fetchall()]
                print(f"     列: {cols[:12]}")
        except Exception as e:
            print(f"  {t}: 失败 {type(e).__name__} {str(e)[:80]}")
finally:
    db.close()
