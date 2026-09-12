#!/usr/bin/env python3
"""
将数据库驱动的 LLMs.txt 写入 `frontend/public/llms.txt`（《立即执行任务完成报告》LLMs.txt 预生成）。
在仓库根执行；需已安装 backend 依赖，使用 backend 当前 DATABASE_URL（默认 SQLite）。
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)


def main() -> None:
    from app.core.database import SessionLocal
    from app.api.v1.seo.llms_txt_generator import build_llms_txt_from_db

    db = SessionLocal()
    try:
        data = build_llms_txt_from_db(db)
    finally:
        db.close()

    out = os.path.join(ROOT, "frontend", "public", "llms.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(data["content"])
    print(f"Wrote {out} ({len(data['content'])} chars, products={data['product_count']})")


if __name__ == "__main__":
    main()
