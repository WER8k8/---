# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块2 最终门禁①：真实 PG 端到端「注入真生效」独立复算（QA 自研）。

不复用白客的脚本或断言：本脚本自建临时租户、走真实管道 run_calculation、
独立硬编码期望值。同一行文案在两套 Profile 下应落到**不同材料 → 不同价**，
两值不同才算注入真生效。

期望（与 team-lead 门禁口径一致）：
- machinery 租户（绑 machinery）行 "steel plate 钢板" × 500 sqm（FOB）
  → steel_plate 基价 420.0 / subtotal 210000.0 / total 203700.0（含 3% MOQ 档）
- 默认租户（未绑 → building_materials）同一行
  → metal 基价 120.0 / subtotal 60000.0 / total 60000.0（无折扣）

用完即清理临时租户及其作业/行项。

用法（真实 PG，非 sqlite）::

    cd backend
    ./.venv/Scripts/python.exe scripts/qa/e2e_machinery_injection_pg.py

退出码 0 = 两值符合且不相同；1 = 不符。
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.models.boq_import import BoqImportJob, BoqLineItem  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.services import boq_pipeline_service as bps  # noqa: E402
from app.services import industry_profile_service as ips  # noqa: E402

PREFIX = "qa-e2e-mach-"
DESC = "steel plate 钢板"     # machinery→steel_plate；默认→metal
QTY = 500


def _mk_tenant(db, code: str, plan_id: str) -> str:
    tid = str(uuid.uuid4())
    db.add(Tenant(id=tid, name=f"{PREFIX}{code}", domain=f"{PREFIX}{code}.example.com",
                  plan_id=plan_id))
    db.commit()
    return tid


def _run_one_line(db, tenant_id: str, *, bind_code=None) -> dict:
    if bind_code:
        ips.set_tenant_profile_code(db, tenant_id, bind_code, actor="qa-e2e")
    job = bps.create_job(db, tenant_id=tenant_id, source_name="qa-e2e",
                         defaults={"incoterms": "FOB"})
    bps.add_manual_lines(db, job, [{"description": DESC, "quantity": QTY, "unit": "sqm"}],
                         extractor="manual")
    bps.run_normalization(db, job)
    line = db.query(BoqLineItem).filter(BoqLineItem.boq_job_id == job.id).first()
    line.review_status = "confirmed"
    db.add(line)
    db.commit()
    result = bps.run_calculation(db, job)
    lr = result["lines"][0]
    return {"job_id": job.id, "line": lr["calc"], "grand_total": result["grand_total_usd"]}


def _cleanup(db, tenant_ids: list[str]) -> None:
    try:
        db.rollback()
    except Exception:  # noqa: BLE001
        pass
    for tid in tenant_ids:
        job_ids = [r[0] for r in db.execute(
            text("SELECT id FROM boq_import_jobs WHERE tenant_id = :t"), {"t": tid}
        ).all()]
        for jid in job_ids:
            db.execute(text("DELETE FROM boq_line_items WHERE boq_job_id = :j"), {"j": jid})
            db.execute(text("DELETE FROM boq_import_jobs WHERE id = :j"), {"j": jid})
        db.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tid})
    db.commit()


def main() -> int:
    Session = sessionmaker(bind=engine)
    db = Session()
    tenant_ids: list[str] = []
    try:
        plan_id = str(db.execute(text("SELECT id FROM tenant_plans ORDER BY created_at LIMIT 1")).scalar())
        if not plan_id:
            raise RuntimeError("tenant_plans 无可用计划行（无法满足 tenants.plan_id FK）")
        t_mach = _mk_tenant(db, "machinery", plan_id)
        t_def = _mk_tenant(db, "default", plan_id)
        tenant_ids = [t_mach, t_def]

        mach = _run_one_line(db, t_mach, bind_code="machinery")
        dflt = _run_one_line(db, t_def)

        print("=" * 78)
        print(f"machinery 租户: base={mach['line']['base_price']} subtotal={mach['line']['subtotal']} total={mach['line']['total']} grand={mach['grand_total']}")
        print(f"default   租户: base={dflt['line']['base_price']} subtotal={dflt['line']['subtotal']} total={dflt['line']['total']} grand={dflt['grand_total']}")
        print("=" * 78)

        checks = [
            ("machinery base_price==420.0", mach["line"]["base_price"] == 420.0),
            ("machinery subtotal==210000.0", mach["line"]["subtotal"] == 210000.0),
            ("machinery total==203700.0", mach["line"]["total"] == 203700.0),
            ("default base_price==120.0", dflt["line"]["base_price"] == 120.0),
            ("default total==60000.0", dflt["line"]["total"] == 60000.0),
            ("两值不同（注入真生效）", mach["line"]["base_price"] != dflt["line"]["base_price"]
                                      and mach["line"]["total"] != dflt["line"]["total"]),
        ]
        fails = 0
        for name, ok in checks:
            if not ok:
                fails += 1
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print("=" * 78)
        print(f"合计 {len(checks)} 项，PASS {len(checks) - fails}，FAIL {fails}")
        return 1 if fails else 0
    finally:
        try:
            _cleanup(db, tenant_ids)
            print(f"清理完成：已删临时租户 {len(tenant_ids)} 个及其作业/行项")
        finally:
            db.close()


if __name__ == "__main__":
    raise SystemExit(main())
