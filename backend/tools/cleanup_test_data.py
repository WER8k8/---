"""测试数据治理工具 —— ③ 缺口补齐。

职责（防测试/联调数据污染生产库，而非一次性清）：
1. scan  扫描标记数据（user_a_* / *@test.local / AUTO_TEST 痕迹）
2. cleanup  dry-run 列出可安全删除项，--apply 才真删（先查外键关联）
3. 约定：新联调数据一律带 tenant_id 前缀 "TEST-"，由本工具识别

用法（在 backend 目录）：
    python tools/cleanup_test_data.py --db youding_dev.db --scan
    python tools/cleanup_test_data.py --db youding_dev.db --cleanup --apply
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from typing import Any, List

# 识别"联调/测试"数据的标记规则（可加）
TEST_PATTERNS = {
    "username": re.compile(r"^user_a_", re.I),
    "email": re.compile(r"@(test\.local|autotest\.local)$", re.I),
    "tenant_id": re.compile(r"^TEST-", re.I),
}


def _cols(cur: sqlite3.Cursor, table: str) -> List[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def scan(conn: sqlite3.Connection) -> dict[str, Any]:
    """扫描并汇总标记数据，不改动。"""
    cur = conn.cursor()
    result: dict[str, Any] = {"hits": {}, "total_marked_users": 0}

    # users 表
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cur.fetchone():
        cols = set(_cols(cur, "users"))
        marked_ids: list[str] = []
        for where_col, pat in (("username", TEST_PATTERNS["username"]),
                               ("email", TEST_PATTERNS["email"])):
            if where_col in cols:
                cur.execute(
                    f"SELECT id, {where_col} FROM users WHERE {where_col} IS NOT NULL"
                )
                rows = [(i, v) for i, v in cur.fetchall() if pat.search(str(v or ""))]
                result["hits"][f"users.{where_col}"] = [
                    {"id": i, "value": v} for i, v in rows
                ]
                marked_ids += [i for i, _ in rows]
        # tenant 前缀
        if "tenant_id" in cols:
            cur.execute("SELECT id, tenant_id FROM users WHERE tenant_id IS NOT NULL")
            rows = [(i, t) for i, t in cur.fetchall() if TEST_PATTERNS["tenant_id"].search(str(t))]
            result["hits"]["users.tenant_id"] = [
                {"id": i, "value": t} for i, t in rows
            ]
            marked_ids += [i for i, _ in rows]
        result["total_marked_users"] = len(set(marked_ids))

    return result


def cleanup(conn: sqlite3.Connection, *, apply: bool = False) -> dict[str, Any]:
    """对标记用户做级联清理（先查外键关联，报告受影响子表；apply 才删）。"""
    cur = conn.cursor()
    report: dict[str, Any] = {"applied": apply, "deleted": 0, "blocked_by": []}

    scan_result = scan(conn)
    marked = set()
    for rows in scan_result["hits"].values():
        marked.update(r["id"] for r in rows)
    report["marked_user_ids"] = sorted(marked)

    if not marked:
        report["message"] = "未发现标记数据，无需清理"
        return report

    # 查哪些子表外键指向 users（用 REFERENCES 解析）
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    referenced_by: list[tuple[str, str]] = []
    for tname, sql in cur.fetchall():
        m = re.search(r"REFERENCES\s+users\s*\(", sql or "", re.I)
        if m:
            referenced_by.append((tname, sql))
    # 统计每个子表受影响行数
    for tname, _sql in referenced_by:
        cur.execute(f"PRAGMA foreign_key_list({tname})")
        fks = [r[2] for r in cur.fetchall() if r[3] == "users"]
        for fkcol in fks:
            cur.execute(
                f"SELECT count(*) FROM {tname} WHERE {fkcol} IN "
                f"({','.join('?' for _ in marked)})",
                tuple(marked),
            )
            n = cur.fetchone()[0]
            if n:
                report.setdefault("referenced_rows", []).append(
                    {"table": tname, "column": fkcol, "count": n}
                )

    if not apply:
        report["message"] = "dry-run：仅列出，未删除。加 --apply 执行。"
        return report

    # 真删：先删子表（按外键顺序），再删 users
    # 注意：SQLite 外键约束默认未必开启，这里按子表→主表顺序删保证一致性
    seen = set()
    for item in report.get("referenced_rows", []):
        tname = item["table"]
        if tname in seen:
            continue
        seen.add(tname)
        cur.execute(
            f"DELETE FROM {tname} WHERE {item['column']} IN "
            f"({','.join('?' for _ in marked)})",
            tuple(marked),
        )
    cur.execute(
        f"DELETE FROM users WHERE id IN ({','.join('?' for _ in marked)})",
        tuple(marked),
    )
    conn.commit()
    report["deleted"] = len(marked)
    report["message"] = f"已清理 {len(marked)} 个标记用户及其关联数据"
    return report


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="测试数据治理")
    ap.add_argument("--db", default="youding_dev.db", help="SQLite 数据库文件")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan", action="store_true", help="只扫描")
    g.add_argument("--cleanup", action="store_true", help="清理（默认 dry-run）")
    ap.add_argument("--apply", action="store_true", help="真正执行删除")
    args = ap.parse_args(argv)

    conn = sqlite3.connect(args.db)
    try:
        if args.scan:
            import json
            print(json.dumps(scan(conn), ensure_ascii=False, indent=2, default=str))
        else:
            import json
            print(json.dumps(cleanup(conn, apply=args.apply),
                             ensure_ascii=False, indent=2, default=str))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
