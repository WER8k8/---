# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P0-7 回填脚本 — 为存量 Company 计算并回写 ICP/Intent/Account 评分。

用法（在本 backend 目录下，激活 venv 后）：
    python scripts/backfill_company_scores.py
    python scripts/backfill_company_scores.py --tenant <tenant_id>   # 仅指定租户
    python scripts/backfill_company_scores.py --dry-run              # 只统计不写入

说明：仅回写三列评分（icp_score/intent_score/account_score）并留痕 IntentEngineRun，
不删除、不修改其它字段。可重复运行（幂等）。
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.company import Company
from app.services.company_scoring_service import score_company


def main() -> int:
    parser = argparse.ArgumentParser(description="回填 Company 评分")
    parser.add_argument("--tenant", default=None, help="仅处理指定 tenant_id")
    parser.add_argument("--dry-run", action="store_true", help="只统计不写入")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        q = db.query(Company)
        if args.tenant:
            q = q.filter(Company.tenant_id == args.tenant)
        rows = q.all()
        total = len(rows)
        scored = 0
        for c in rows:
            if args.dry_run:
                from app.services.company_scoring_service import (
                    compute_account_score,
                    compute_icp_score,
                    compute_intent_score,
                )
                icp, _ = compute_icp_score(c)
                intent, _ = compute_intent_score(db, c)
                account, _ = compute_account_score(c)
                print(f"[dry-run] {c.id} {c.name!r}: icp={icp} intent={intent} account={account}")
                scored += 1
            else:
                score_company(db, c)
                scored += 1
        print(f"完成：共 {total} 家公司，已处理 {scored} 家（dry_run={args.dry_run}）")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"回填失败: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
