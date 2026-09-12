"""轮22 MeterEvent 埋点 + 财务对账 内存 SQLite 全流程验证（不触碰真实 DB）。

用法：python -m tests.meter_reconcile_verify
依赖：sqlalchemy（已装）；无需 pytest / pydantic。

沿用 shim 模式——预置假的 app.core.database / app.core.config，绕开重型依赖，
直接从文件加载被测模块。覆盖：7 类埋点、幂等、汇总进 token_ledger / finance_ledger、
对账误差 0、配额走 plan_gate_service、跨租户隔离。
"""

import os
import sys
import types
import importlib.util
from datetime import datetime, timedelta, timezone

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class _Base(DeclarativeBase):
    pass


DB_SHIM.Base = _Base
DB_SHIM.UUID_TYPE = String(36)
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim（依赖链兜底）----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "meter-reconcile-verify-secret-2026"
    MODEL_GATEWAY_ENABLED = False
    EVOLUTION_TRACE_ENABLED = False
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND)


def _new_dummy(mod_name: str) -> types.ModuleType:
    mod = types.ModuleType(mod_name)
    mod.__path__ = []
    sys.modules[mod_name] = mod
    return mod


def _load_from_file(mod_name: str, path: str):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_MODELS = os.path.join(_BACKEND, "app", "models")

for _pkg in (
    "app",
    "app.core",
    "app.models",
    "app.services",
    "app.services.billing",
    "app.api",
    "app.api.v1",
    "app.api.v1.admin_bff",
):
    _new_dummy(_pkg)

# plan_gate_service 依赖：plan_catalog 为真实现；app.models.tenant 仅作类型注解，给空类
_load_from_file(
    "app.api.v1.admin_bff.plan_catalog",
    os.path.join(_BACKEND, "app", "api", "v1", "admin_bff", "plan_catalog.py"),
)
_tenant_dummy = _new_dummy("app.models.tenant")


class _TenantType:
    pass


_tenant_dummy.Tenant = _TenantType

_meter_models = _load_from_file(
    "app.models.meter", os.path.join(_MODELS, "meter.py")
)
_tl_models = _load_from_file(
    "app.models.token_ledger", os.path.join(_MODELS, "token_ledger.py")
)
_fl_models = _load_from_file(
    "app.models.finance_ledger", os.path.join(_MODELS, "finance_ledger.py")
)

_meter_svc = _load_from_file(
    "app.services.billing.meter_event",
    os.path.join(_BACKEND, "app", "services", "billing", "meter_event.py"),
)
_plan_gate = _load_from_file(
    "app.services.plan_gate_service",
    os.path.join(_BACKEND, "app", "services", "plan_gate_service.py"),
)

MeterEvent = _meter_models.MeterEvent
METER_TYPES = _meter_models.METER_TYPES
TokenLedgerEntry = _tl_models.TokenLedgerEntry
FinanceLedgerEntry = _fl_models.FinanceLedgerEntry
MeterEventService = _meter_svc.MeterEventService
evaluate_ai_quota = _plan_gate.evaluate_ai_quota

# ---- 外部依赖表桩（FK 解析）----
from sqlalchemy.orm import mapped_column  # noqa: E402


class TenantShim(_Base):
    __tablename__ = "tenants"
    id = mapped_column(String(36), primary_key=True)


_passed = 0
_failed = 0


def check(name: str, cond: bool, detail: str = ""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}  {detail}")


def _setup_db():
    engine = create_engine("sqlite:///:memory:")
    _Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def main() -> int:
    db: Session = _setup_db()
    svc = MeterEventService(db)
    tenant_a = "tenant-a-0001"
    tenant_b = "tenant-b-0002"

    # ============ 1. 7 类埋点 + 非法类型 + 幂等 ============
    print("== 1. 7 类埋点与幂等 ==")
    emitted = {}
    emitted["ai_generation"] = svc.emit_ai_generation(
        tenant_id=tenant_a, event_key="ev-ai-1", token_delta=1200, cost_cents=30,
        model_name="qwen-max", source_ref_id="task-1",
    )
    emitted["content_publish"] = svc.emit_content_publish(
        tenant_id=tenant_a, event_key="ev-cp-1", cost_cents=100, source_ref_id="content-1",
    )
    emitted["lead_generated"] = svc.emit_lead_generated(
        tenant_id=tenant_a, event_key="ev-lg-1", cost_cents=200, source_ref_id="lead-1",
    )
    emitted["rfq_created"] = svc.emit_rfq_created(
        tenant_id=tenant_a, event_key="ev-rfq-1", cost_cents=300, source_ref_id="rfq-1",
    )
    emitted["api_call"] = svc.emit_api_call(
        tenant_id=tenant_a, event_key="ev-api-1", cost_cents=50, source_ref_id="api-1",
    )
    emitted["export"] = svc.emit_export(
        tenant_id=tenant_a, event_key="ev-exp-1", cost_cents=80, source_ref_id="export-1",
    )
    emitted["video_job"] = svc.emit_video_job(
        tenant_id=tenant_a, event_key="ev-vid-1", cost_cents=500, source_ref_id="video-1",
    )
    check("7 类埋点全部写入", db.query(MeterEvent).count() == 7,
          f"count={db.query(MeterEvent).count()}")
    check("7 类动作类型齐全", {e.meter_type for e in db.query(MeterEvent).all()} == set(METER_TYPES))

    try:
        svc.emit(meter_type="not_a_type", tenant_id=tenant_a)
        check("非法埋点类型被拒绝", False)
    except ValueError:
        check("非法埋点类型被拒绝", True)

    dup = svc.emit_ai_generation(
        tenant_id=tenant_a, event_key="ev-ai-1", token_delta=99999,
    )
    check("event_key 幂等去重", dup.id == emitted["ai_generation"].id,
          f"dup={dup.id} orig={emitted['ai_generation'].id}")
    check("幂等不覆盖原事件", dup.token_delta == 1200, f"delta={dup.token_delta}")

    # ============ 2. ai_generation → token_ledger 汇总 ============
    print("== 2. ai_generation 汇总进 token_ledger ==")
    agg1 = svc.aggregate_to_billing(tenant_id=tenant_a)
    check("ai_generation 汇总 1 条", agg1["token_events"] == 1, f"agg={agg1}")
    check("token 扣减量正确", agg1["token_delta"] == 1200, f"agg={agg1}")
    check("营收类汇总 6 条", agg1["finance_events"] == 6, f"agg={agg1}")
    check("营收金额正确", agg1["finance_cents"] == 100 + 200 + 300 + 50 + 80 + 500,
          f"agg={agg1}")

    tl_rows = db.query(TokenLedgerEntry).all()
    check("token_ledger 写入 1 条流水", len(tl_rows) == 1, f"n={len(tl_rows)}")
    check("token 扣减为负", tl_rows[0].delta == -1200, f"delta={tl_rows[0].delta}")
    check("token balance_after 正确", tl_rows[0].balance_after == -1200,
          f"balance={tl_rows[0].balance_after}")
    check("token 引用 meter 事件", tl_rows[0].reference_id == emitted["ai_generation"].id,
          f"ref={tl_rows[0].reference_id}")

    fl_rows = db.query(FinanceLedgerEntry).all()
    check("finance_ledger 写入 6 条营收", len(fl_rows) == 6, f"n={len(fl_rows)}")
    cats = {r.category for r in fl_rows}
    check("营收分类按动作映射",
          cats == {"content_publish", "lead", "rfq", "api", "export", "video"}, f"cats={cats}")
    check("全部事件已标记汇总",
          db.query(MeterEvent).filter(MeterEvent.aggregated_at.is_(None)).count() == 0)

    # ============ 3. 幂等汇总（重复调用不产生新流水）============
    print("== 3. 幂等汇总 ==")
    agg2 = svc.aggregate_to_billing(tenant_id=tenant_a)
    check("重复汇总不新增", agg2["token_events"] == 0 and agg2["finance_events"] == 0,
          f"agg={agg2}")
    check("账本流水数不变",
          db.query(TokenLedgerEntry).count() == 1
          and db.query(FinanceLedgerEntry).count() == 6)

    # ============ 4. 对账误差 0 ============
    print("== 4. 对账误差 0 ==")
    r1 = svc.reconcile(tenant_id=tenant_a)
    check("ai_generation 对账误差 0", r1["ai_generation"]["difference"] == 0,
          f"diff={r1['ai_generation']['difference']}")
    check("营收对账误差 0", r1["revenue"]["difference"] == 0,
          f"diff={r1['revenue']['difference']}")
    check("无未汇总事件", r1["pending_events"] == 0, f"pending={r1['pending_events']}")
    check("对账误差 0 结论成立", r1["error_free"] is True, f"disc={r1['discrepancies']}")

    # ============ 5. 未汇总事件 → 对账不通过 ============
    print("== 5. 未汇总事件对账拦截 ==")
    svc.emit_content_publish(
        tenant_id=tenant_a, event_key="ev-cp-2", cost_cents=999, source_ref_id="content-2",
    )
    r2 = svc.reconcile(tenant_id=tenant_a)
    check("未汇总事件被捕获", r2["pending_events"] == 1, f"pending={r2['pending_events']}")
    check("未汇总时误差非 0", r2["revenue"]["difference"] == 999,
          f"diff={r2['revenue']['difference']}")
    check("未汇总时 error_free=False", r2["error_free"] is False)
    # 汇总后再次对账 → 误差归 0
    svc.aggregate_to_billing(tenant_id=tenant_a)
    r3 = svc.reconcile(tenant_id=tenant_a)
    check("汇总后对账误差归 0", r3["error_free"] is True, f"disc={r3['discrepancies']}")

    # ============ 6. 跨租户隔离 ============
    print("== 6. 跨租户隔离 ==")
    svc.emit_ai_generation(
        tenant_id=tenant_b, event_key="ev-ai-b1", token_delta=500,
    )
    rA = svc.reconcile(tenant_id=tenant_a)
    rB = svc.reconcile(tenant_id=tenant_b)
    check("租户 A 不含租户 B 事件",
          rA["pending_events"] == 0 and rA["ai_generation"]["metered_token_delta"] == 1200,
          f"A={rA['pending_events']}")
    check("租户 B 单独计量", rB["ai_generation"]["metered_token_delta"] == 500,
          f"B={rB['ai_generation']['metered_token_delta']}")
    svc.aggregate_to_billing(tenant_id=tenant_b)
    check("租户 B 汇总后 token 扣减",
          db.query(TokenLedgerEntry).filter(TokenLedgerEntry.tenant_id == tenant_b).count() == 1)

    # ============ 7. 配额走 plan_gate_service ============
    print("== 7. 配额判定（plan_gate_service）==")
    from types import SimpleNamespace

    pro_plan = SimpleNamespace(code="pro", max_ai_quota=100)
    pro_tenant = SimpleNamespace(plan=pro_plan, ai_quota_used=30)
    q1 = evaluate_ai_quota(pro_tenant)
    check("pro 套餐+额度充足 → 允许", q1["allowed"] is True, f"q={q1}")
    check("剩余额度计算正确", q1["remaining"] == 70, f"remaining={q1['remaining']}")

    exhausted = SimpleNamespace(plan=pro_plan, ai_quota_used=100)
    q2 = evaluate_ai_quota(exhausted)
    check("额度耗尽 → 拒绝", q2["allowed"] is False, f"q={q2}")

    trial_plan = SimpleNamespace(code="trial", max_ai_quota=0)
    trial_tenant = SimpleNamespace(plan=trial_plan, ai_quota_used=0)
    q3 = evaluate_ai_quota(trial_tenant)
    check("体验版无 AI 能力 → 拒绝", q3["allowed"] is False, f"q={q3}")

    # ============ 汇总 ============
    print(f"\n结果: {_passed} PASS / {_failed} FAIL")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
