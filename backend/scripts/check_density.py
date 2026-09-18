import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from sqlalchemy import text

def check_density():
    db = SessionLocal()
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    try:
        tables = [t[0] for t in db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")).fetchall()]
        counts = {}
        for t in tables:
            try:
                cnt = db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar()
                counts[t] = cnt
            except Exception as e:
                counts[t] = -1

        populated = {t: c for t, c in counts.items() if c > 0}
        empty = [t for t, c in counts.items() if c == 0]
        pct = len(populated) / len(tables) * 100 if tables else 0

        print("==================================================")
        print("[REPORT] PostgreSQL 15.8 @5433 Table Density Report")
        print("==================================================")
        print(f"总物理表数: {len(tables)}")
        print(f"非空有效表数: {len(populated)} ({pct:.1f}%)")
        print(f"空表数量: {len(empty)}")
        print(f"==================================================")
        if empty:
            print("目前仍为空的表列表:")
            for i, tbl in enumerate(empty, 1):
                print(f"  {i}. {tbl}")
    finally:
        db.close()

if __name__ == "__main__":
    check_density()
