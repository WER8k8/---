# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""R-4 数据订正：finance_ledger_entries.entry_type 脏词归一（income→revenue / expense→cost）。

背景（2026-09-27 P0-3 实证）：种子 seed_finance_billing_licenses.py 历史
写入 income/expense，与代码标准词表 {revenue, cost} 漂移，导致营收/成本统计
读不到任何行（账上有钱、报表为零）。冻结裁定 R-4 =
「读侧归一（已落地，见 app/models/finance_ledger.py::ENTRY_TYPE_*）
 + 数据订正（本脚本：先备份原行 JSON，再 UPDATE，附反向语句）」。

用法（backend/ 下执行）：
    python scripts/fix_finance_entry_type_2026_09_28.py            # 备份 + 订正
    python scripts/fix_finance_entry_type_2026_09_28.py --reverse  # 按备份 JSON 反向恢复
    python scripts/fix_finance_entry_type_2026_09_28.py --dry-run  # 只备份不更新

幂等：无脏行时直接退出（nothing to fix）。RLS 说明：本脚本走 SessionLocal
（表属主连接），不受 finance_ledger_entries_tenant_isolation 的 app_user 策略限制。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BACKUP_PATH = Path(__file__).resolve().parent / "qa" / "finance_entry_type_backup_2026-09-28.json"

DIRTY_TO_CANONICAL = {"income": "revenue", "expense": "cost"}


def _serialize(row) -> dict:
    return {
        "id": str(row.id),
        "entry_type": row.entry_type,
        "category": row.category,
        "amount_cents": row.amount_cents,
        "tenant_id": str(row.tenant_id) if row.tenant_id else None,
        "reference_id": row.reference_id,
        "note": row.note,
        "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只备份，不执行 UPDATE")
    parser.add_argument("--reverse", action="store_true", help="按备份 JSON 反向恢复")
    args = parser.parse_args()

    import os

    os.environ.setdefault("SECRET_KEY", "dev_secret_key_12345678901234567890123456789012")
    os.environ.setdefault("JWT_SECRET_KEY", "dev_jwt_key_12345678901234567890123456789012")
    os.environ.setdefault("REDIS_ENABLED", "false")
    os.environ.setdefault("ENV", "development")

    from app.db.session import SessionLocal
    from app.models.finance_ledger import FinanceLedgerEntry

    db = SessionLocal()
    try:
        if args.reverse:
            if not BACKUP_PATH.exists():
                print(f"✗ 找不到备份文件：{BACKUP_PATH}")
                return 1
            rows = json.loads(BACKUP_PATH.read_text(encoding="utf-8"))["rows"]
            fixed = 0
            for r in rows:
                target = db.query(FinanceLedgerEntry).filter(
                    FinanceLedgerEntry.id == r["id"]
                ).first()
                if target is None:
                    print(f"  跳过（行已不存在）：{r['id']}")
                    continue
                target.entry_type = r["entry_type"]
                fixed += 1
            db.commit()
            print(f"✓ 反向恢复完成：{fixed} 行还原为 {sorted({r['entry_type'] for r in rows})}")
            return 0

        dirty = (
            db.query(FinanceLedgerEntry)
            .filter(FinanceLedgerEntry.entry_type.in_(list(DIRTY_TO_CANONICAL)))
            .all()
        )
        if not dirty:
            print("✓ nothing to fix：库内已无 income/expense 脏行")
            return 0

        BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "count": len(dirty),
            "reverse_sql": [
                f"UPDATE finance_ledger_entries SET entry_type='{r.entry_type}' WHERE id='{r.id}';"
                for r in dirty
            ],
            "rows": [_serialize(r) for r in dirty],
        }
        BACKUP_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✓ 已备份 {len(dirty)} 行原值 → {BACKUP_PATH}")

        if args.dry_run:
            print("✓ dry-run：未执行 UPDATE")
            return 0

        fixed = 0
        for row in dirty:
            row.entry_type = DIRTY_TO_CANONICAL[row.entry_type]
            fixed += 1
        db.commit()
        print(f"✓ 订正完成：{fixed} 行 income→revenue / expense→cost")
        print("  反向语句已写入备份 JSON 的 reverse_sql 字段；亦可运行 --reverse 一键还原")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
