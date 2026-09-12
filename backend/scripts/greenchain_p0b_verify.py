#!/usr/bin/env python
"""P0-B 绿色 PG 部署链测量：空库 001→heads 全量 upgrade。

用法（backend/ 目录下，用 .venv python）：
    python scripts/greenchain_p0b_verify.py            # 跑全链并报告
    python scripts/greenchain_p0b_verify.py --keep     # 成功后保留临时库供类型审查

行为：
- 在 youding-dev-postgres(5433, pgvector 镜像) 上创建一次性空库 youding_green_p0b
- alembic upgrade heads，成功则 dump PG 下所有 *id 列实际类型（核对 uuid 一致性）
- 崩溃则打印最后应用的 revision、下一个待应用 revision、原始错误
- 退出码 0=全绿 / 1=链崩溃 / 2=环境错误
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import psycopg2

BACKEND = Path(__file__).resolve().parents[1]
ADMIN_URL = "postgresql://youding:youding@localhost:5433/postgres"
GREEN_DB = "youding_green_p0b"


def fresh_db() -> None:
    conn = psycopg2.connect(ADMIN_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {GREEN_DB} WITH (FORCE)")
    cur.execute(f"CREATE DATABASE {GREEN_DB}")
    conn.close()


def run_upgrade() -> tuple[int, str]:
    env = dict(os.environ)
    env["DATABASE_URL"] = f"postgresql://youding:youding@localhost:5433/{GREEN_DB}"
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "heads"],
        cwd=BACKEND, env=env, capture_output=True, text=True, timeout=600,
    )
    return proc.returncode, proc.stdout + proc.stderr


def current_and_next() -> tuple[str, str]:
    """已 stamp 到的 head + 链上下一个 revision（读 versions 文件推 down_revision）。"""
    env = dict(os.environ)
    env["DATABASE_URL"] = f"postgresql://youding:youding@localhost:5433/{GREEN_DB}"
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        cwd=BACKEND, env=env, capture_output=True, text=True,
    )
    stamped = proc.stdout.strip().splitlines()
    cur = stamped[-1].split(" ")[0] if stamped else "(none)"
    nxt = "?"
    for f in (BACKEND / "alembic_migrations" / "versions").glob("*.py"):
        txt = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'^down_revision[^=]*=\s*["\']([^"\']+)["\']', txt, re.M)
        if m and m.group(1) == cur:
            mr = re.search(r'^revision[^=]*=\s*["\']([^"\']+)["\']', txt, re.M)
            nxt = mr.group(1) if mr else "?"
            break
    return cur, nxt


def report_id_types() -> None:
    conn = psycopg2.connect(f"postgresql://youding:youding@localhost:5433/{GREEN_DB}")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name, data_type, count(*)
        FROM information_schema.columns
        WHERE column_name LIKE '%\\_id' OR (column_name = 'id' AND table_schema = 'public')
        GROUP BY table_name, data_type
        HAVING count(*) > 0
        ORDER BY data_type, table_name
        """
    )
    rows = cur.fetchall()
    varchar_ids = sorted({t for t, d, _ in rows if d == "character varying"})
    print(f"\nPG 实际 id 列类型分布：uuid 表 {len({t for t, d, _ in rows if d == 'uuid'})} 张，"
          f"varchar 残留 {len(varchar_ids)} 张")
    if varchar_ids:
        print("  varchar id 残留表：" + ", ".join(varchar_ids))
    # FK 类型错配核查（PG catalog 直查，跨表引用类型不一致 = 建链时必炸或已绕炸）
    cur.execute(
        """
        SELECT con.conname, cl.relname AS child, att.attname,
               cls.relname AS parent, ptt.attname AS parent_col,
               t1.typname AS child_type, t2.typname AS parent_type
        FROM pg_constraint con
        JOIN pg_class cl ON cl.oid = con.conrelid
        JOIN pg_attribute att ON att.attrelid = cl.oid AND att.attnum = con.conkey[1]
        JOIN pg_class cls ON cls.oid = con.confrelid
        JOIN pg_attribute ptt ON ptt.attrelid = cls.oid AND ptt.attnum = con.confkey[1]
        JOIN pg_type t1 ON t1.oid = att.atttypid
        JOIN pg_type t2 ON t2.oid = ptt.atttypid
        WHERE con.contype = 'f' AND t1.typname <> t2.typname
        """
    )
    mismatches = cur.fetchall()
    print(f"FK 类型错配：{len(mismatches)} 处")
    for m in mismatches[:10]:
        print(f"  {m[0]}: {m[1]}.{m[2]}({m[5]}) -> {m[3]}.{m[4]}({m[6]})")
    conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="成功后保留临时库")
    ap.add_argument("--no-fresh", action="store_true", help="不清库，从当前状态续跑")
    args = ap.parse_args()

    try:
        if not args.no_fresh:
            fresh_db()
    except Exception as e:
        print(f"[ENV] 建库失败：{e}")
        return 2

    rc, out = run_upgrade()
    if rc == 0:
        print(f"[PASS] 绿色链 001→heads 全绿（库 {GREEN_DB}）")
        report_id_types()
        if not args.keep:
            conn = psycopg2.connect(ADMIN_URL)
            conn.autocommit = True
            conn.cursor().execute(f"DROP DATABASE {GREEN_DB} WITH (FORCE)")
            conn.close()
        return 0

    cur, nxt = current_and_next()
    print(f"[FAIL] upgrade 崩溃：最后 applied={cur}，下一个={nxt}")
    err_lines = [l for l in out.splitlines() if l.strip()][-30:]
    print("\n".join(err_lines))
    return 1


if __name__ == "__main__":
    sys.exit(main())
