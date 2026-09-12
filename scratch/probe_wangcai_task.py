# -*- coding: utf-8 -*-
"""H.5 实测探针：查 wangcai_intent 任务面落库状态。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.db.session import engine

rows = engine.connect().execute(
    text(
        "SELECT id, status, source, task_type, "
        "left(coalesce(output_json,''),300) AS out, error_message "
        "FROM ai_tasks WHERE task_type='wangcai_intent' "
        "ORDER BY created_at DESC LIMIT 3"
    )
).fetchall()
if not rows:
    print("NO wangcai_intent task rows yet")
for r in rows:
    print(r[0], "|", r[1], "|", r[2], "|", r[3])
    print("  out:", r[4])
    print("  err:", r[5])
