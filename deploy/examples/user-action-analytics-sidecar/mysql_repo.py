"""MySQL 读写 — 与上游 UserActionAnalyzePlatform task/结果表对齐。"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator

import pymysql


def _mysql_config() -> dict[str, Any]:
    dsn = (os.getenv("USER_ACTION_ANALYTICS_MYSQL_DSN") or "").strip()
    if dsn.startswith("mysql://"):
        # mysql://user:pass@host:3306/db
        from urllib.parse import urlparse

        u = urlparse(dsn)
        return {
            "host": u.hostname or "127.0.0.1",
            "port": u.port or 3306,
            "user": u.username or "root",
            "password": u.password or "",
            "database": (u.path or "/user_action_analytics").lstrip("/"),
            "charset": "utf8mb4",
        }
    return {
        "host": os.getenv("USER_ACTION_MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("USER_ACTION_MYSQL_PORT", "3306")),
        "user": os.getenv("USER_ACTION_MYSQL_USER", "uaa"),
        "password": os.getenv("USER_ACTION_MYSQL_PASSWORD", "uaa_dev"),
        "database": os.getenv("USER_ACTION_MYSQL_DB", "user_action_analytics"),
        "charset": "utf8mb4",
    }


@contextmanager
def connect() -> Generator[pymysql.connections.Connection, None, None]:
    conn = pymysql.connect(**_mysql_config())
    try:
        yield conn
    finally:
        conn.close()


def create_task(
    *,
    task_type: str,
    task_name: str,
    task_param: dict[str, Any],
) -> int:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO task (task_name, create_time, start_time, task_type, task_status, task_param)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    task_name,
                    now,
                    now,
                    task_type,
                    "running",
                    json.dumps(task_param, ensure_ascii=False),
                ),
            )
            conn.commit()
            return int(cur.lastrowid)


def finish_task(task_id: int, status: str) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE task SET task_status=%s, finish_time=%s WHERE task_id=%s",
                (status, now, task_id),
            )
        conn.commit()


def fetch_session_aggr(task_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT * FROM session_aggr_stat WHERE task_id=%s", (task_id,))
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_top10_category(task_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                "SELECT * FROM top10_category WHERE task_id=%s ORDER BY click_count DESC LIMIT 10",
                (task_id,),
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_page_conversion(task_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                """
                SELECT from_page, to_page, transition_count, conversion_rate
                FROM page_conversion_stat WHERE task_id=%s
                ORDER BY conversion_rate DESC LIMIT 50
                """,
                (task_id,),
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def compute_page_conversion_from_session_detail(task_id: int) -> list[dict[str, Any]]:
    """从 session_detail 计算单跳转化（上游 README 模块 2 的 Sidecar 实现）。"""
    with connect() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                """
                SELECT session_id, page_id, action_time
                FROM session_detail WHERE task_id=%s AND page_id IS NOT NULL
                ORDER BY session_id, action_time
                """,
                (task_id,),
            )
            rows = cur.fetchall()

    from collections import defaultdict

    transitions: dict[tuple[str, str], int] = defaultdict(int)
    from_totals: dict[str, int] = defaultdict(int)
    last_page: dict[str, str] = {}
    for row in rows:
        sid = str(row["session_id"])
        page = str(row["page_id"])
        prev = last_page.get(sid)
        if prev and prev != page:
            transitions[(prev, page)] += 1
            from_totals[prev] += 1
        last_page[sid] = page

    items: list[dict[str, Any]] = []
    with connect() as conn:
        with conn.cursor() as cur:
            for (fp, tp), cnt in transitions.items():
                rate = cnt / from_totals[fp] if from_totals[fp] else 0.0
                cur.execute(
                    """
                    INSERT INTO page_conversion_stat
                    (task_id, from_page, to_page, transition_count, conversion_rate)
                    VALUES (%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                    transition_count=VALUES(transition_count),
                    conversion_rate=VALUES(conversion_rate)
                    """,
                    (task_id, fp, tp, cnt, rate),
                )
                items.append(
                    {
                        "from_page": fp,
                        "to_page": tp,
                        "transition_count": cnt,
                        "conversion_rate": round(rate, 4),
                    }
                )
        conn.commit()
    items.sort(key=lambda x: x["conversion_rate"], reverse=True)
    return items
