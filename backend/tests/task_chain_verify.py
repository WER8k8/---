"""轮23 任务端接线 内存 SQLite 全流程验证（不触碰真实 DB）。

用法：python -m tests.task_chain_verify
依赖：sqlalchemy（已装）；无需 pytest / pydantic。

沿用 shim 模式——预置假的 app.core.database / app.core.config，绕开重型依赖，
直接从文件加载被测模块。覆盖：ai_tasks 11 态状态机（终态冻结/有界重试/非法转移
拒绝）、create 幂等 + 预算门、任务全链路 create→start→complete/fail→Trace→
terminal_hook(evolution)→Meter、开关关闭时副作用跳过、跨租户隔离、
Model Gateway 成功路径 ai_generation 计量旁路、计量→token_ledger 对账收口。
"""

import asyncio
import os
import sys
import types
import importlib.util
from types import SimpleNamespace

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class _Base(DeclarativeBase):
    pass


DB_SHIM.Base = _Base
DB_SHIM.UUID_TYPE = String(36)
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim（TASK_CONTROL_ENABLED 可切换）----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "task-chain-verify-secret-2026"
    MODEL_GATEWAY_ENABLED = False
    EVOLUTION_TRACE_ENABLED = False
    TASK_CONTROL_ENABLED = False
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
_SERVICES = os.path.join(_BACKEND, "app", "services")

for _pkg in (
    "app",
    "app.core",
    "app.models",
    "app.services",
    "app.services.billing",
    "app.services.trace",
    "app.services.tasks",
    "app.services.model_gateway",
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

# ---- 模型（真实实现）----
_ai_task_models = _load_from_file(
    "app.models.ai_task", os.path.join(_MODELS, "ai_task.py")
)
_trace_models = _load_from_file(
    "app.models.trace", os.path.join(_MODELS, "trace.py")
)
_evo_models = _load_from_file(
    "app.models.evolution", os.path.join(_MODELS, "evolution.py")
)
_meter_models = _load_from_file(
    "app.models.meter", os.path.join(_MODELS, "meter.py")
)
_tl_models = _load_from_file(
    "app.models.token_ledger", os.path.join(_MODELS, "token_ledger.py")
)
_fl_models = _load_from_file(
    "app.models.finance_ledger", os.path.join(_MODELS, "finance_ledger.py")
)

# ---- 服务（真实实现，按依赖顺序）----
_meter_svc_mod = _load_from_file(
    "app.services.billing.meter_event",
    os.path.join(_SERVICES, "billing", "meter_event.py"),
)
_trace_svc_mod = _load_from_file(
    "app.services.trace.trace_service",
    os.path.join(_SERVICES, "trace", "trace_service.py"),
)
_terminal_hook_mod = _load_from_file(
    "app.services.trace.terminal_hook",
    os.path.join(_SERVICES, "trace", "terminal_hook.py"),
)
_plan_gate = _load_from_file(
    "app.services.plan_gate_service",
    os.path.join(_SERVICES, "plan_gate_service.py"),
)
_task_control_mod = _load_from_file(
    "app.services.tasks.task_control",
    os.path.join(_SERVICES, "tasks", "task_control.py"),
)

# ---- Model Gateway（真实实现：capability → router → ledger → gateway）----
_cap_mod = _load_from_file(
    "app.services.model_gateway.capability",
    os.path.join(_SERVICES, "model_gateway", "capability.py"),
)
_router_mod = _load_from_file(
    "app.services.model_gateway.router",
    os.path.join(_SERVICES, "model_gateway", "router.py"),
)
_gw_ledger_mod = _load_from_file(
    "app.services.model_gateway.ledger",
    os.path.join(_SERVICES, "model_gateway", "ledger.py"),
)
_gateway_mod = _load_from_file(
    "app.services.model_gateway.gateway",
    os.path.join(_SERVICES, "model_gateway", "gateway.py"),
)

# ---- ai_engine 桩（gateway.generate 懒导入 get_ai_engine）----
_ai_engine_stub = _new_dummy("app.services.ai_engine")


class _StubEngine:
    async def generate(self, prompt, *, model=None, max_tokens=1000,
                       task_complexity="medium", max_retries=3):
        return {"content": "ok", "token_usage": 123, "cost": 0.05,
                "model": model or "qwen-max"}


_ai_engine_stub.get_ai_engine = lambda: _StubEngine()

# ---- 被测符号 ----
AiTask = _ai_task_models.AiTask
TASK_STATUSES = _ai_task_models.TASK_STATUSES
TaskTrace = _trace_models.TaskTrace
SkillPerformance = _trace_models.SkillPerformance
ExperienceEntry = _evo_models.ExperienceEntry
EvolutionTaskRecord = _evo_models.EvolutionTaskRecord
MeterEvent = _meter_models.MeterEvent
TokenLedgerEntry = _tl_models.TokenLedgerEntry

TaskControlService = _task_control_mod.TaskControlService
InvalidTaskTransition = _task_control_mod.InvalidTaskTransition
QuotaGateDenied = _task_control_mod.QuotaGateDenied
TaskNotFound = _task_control_mod.TaskNotFound
can_transition = _task_control_mod.can_transition
TRANSITIONS = _task_control_mod.TRANSITIONS
MeterEventService = _meter_svc_mod.MeterEventService
evaluate_ai_quota = _plan_gate.evaluate_ai_quota
ModelGateway = _gateway_mod.ModelGateway


# ---- 外部依赖表桩（FK 解析）----
class TenantShim(_Base):
    __tablename__ = "tenants"
    id = mapped_column(String(36), primary_key=True)


# StaticPool：单连接跨线程共享（gateway 旁路埋点经 to_thread 写同一内存库）
_engine = create_engine(
    "sqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
DB_SHIM.SessionLocal = sessionmaker(bind=_engine)
_Base.metadata.create_all(_engine)

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


def _set_flag(on: bool) -> None:
    CFG_SHIM.settings.TASK_CONTROL_ENABLED = on


def _db() -> Session:
    return sessionmaker(bind=_engine)()


def _fresh_count(model, **filters) -> int:
    with DB_SHIM.SessionLocal() as s:
        q = s.query(model)
        for k, v in filters.items():
            q = q.filter(getattr(model, k) == v)
        return q.count()


def main() -> int:
    db: Session = _db()
    svc = TaskControlService(db)
    tenant_a = "tenant-a-0001"
    tenant_b = "tenant-b-0002"
    tenant_c = "tenant-c-0003"

    pro_plan = SimpleNamespace(code="pro", max_ai_quota=100)
    ok_tenant = SimpleNamespace(plan=pro_plan, ai_quota_used=30)
    exhausted = SimpleNamespace(plan=pro_plan, ai_quota_used=100)
    trial_tenant = SimpleNamespace(
        plan=SimpleNamespace(code="trial", max_ai_quota=0), ai_quota_used=0
    )

    # ============ 1. 状态机转移矩阵（纯逻辑） ============
    print("== 1. 状态机转移矩阵 ==")
    check("11 态全覆盖", set(TRANSITIONS.keys()) == set(TASK_STATUSES),
          f"keys={sorted(TRANSITIONS.keys())}")
    main_path_ok = all(
        can_transition(a, b) for a, b in [
            ("created", "planning"), ("planning", "executing"),
            ("executing", "review"), ("review", "done"),
        ]
    )
    check("主链 created→planning→executing→review→done 合法", main_path_ok)
    check("created 可直入 executing", can_transition("created", "executing"))
    check("终态 done 不可再转移",
          all(not can_transition("done", s) for s in TASK_STATUSES if s != "done"))
    check("终态 failed/cancelled/timeout 均为空集",
          all(not TRANSITIONS[s] for s in ("failed", "cancelled", "timeout")))
    check("created→done 非法", not can_transition("created", "done"))
    check("executing→planning 非法（不可回退）",
          not can_transition("executing", "planning"))
    check("paused→executing 合法（恢复）", can_transition("paused", "executing"))
    check("wait_human→executing 合法（人工放行）",
          can_transition("wait_human", "executing"))
    check("executing→retrying 合法", can_transition("executing", "retrying"))

    # ============ 2. create 幂等 + 预算门 ============
    print("== 2. create 幂等 + 预算门 ==")
    t1 = svc.create_task(
        tenant_id=tenant_a, task_type="ai_content_generate",
        input_data={"topic": "轻集料混凝土"}, idempotency_key="idem-1",
        budget_limit=5.0, source="wangcai", tenant=ok_tenant,
    )
    check("AI 任务（额度充足）创建成功", t1.status == "created")
    t1_dup = svc.create_task(
        tenant_id=tenant_a, task_type="ai_content_generate",
        idempotency_key="idem-1", tenant=ok_tenant,
    )
    check("幂等键去重返回既有任务", t1_dup.id == t1.id)
    check("幂等不重复建行",
          _fresh_count(AiTask, tenant_id=tenant_a) == 1)
    try:
        svc.create_task(
            tenant_id=tenant_a, task_type="ai_content_generate",
            idempotency_key="idem-2", tenant=exhausted,
        )
        check("额度耗尽 → 预算门拒绝", False)
    except QuotaGateDenied:
        check("额度耗尽 → 预算门拒绝", True)
    try:
        svc.create_task(
            tenant_id=tenant_a, task_type="ai_content_generate",
            idempotency_key="idem-3", tenant=trial_tenant,
        )
        check("体验版无 AI 能力 → 预算门拒绝", False)
    except QuotaGateDenied:
        check("体验版无 AI 能力 → 预算门拒绝", True)
    t_np = svc.create_task(
        tenant_id=tenant_b, task_type="content_publish",
        idempotency_key="idem-b1", tenant=exhausted,
    )
    check("非 AI 任务类型跳过预算门", t_np.status == "created")

    # ============ 3. 成功全链路（开关开） ============
    print("== 3. 成功全链路：create→start→complete→Trace→Meter→Evolution ==")
    _set_flag(True)
    t2 = svc.create_task(
        tenant_id=tenant_a, task_type="ai_copywrite",
        input_data={"brief": "产品文案"}, idempotency_key="idem-4",
        source="wangcai", tenant=ok_tenant,
    )
    t2 = svc.start_task(
        t2.id, executor_type="skill", skill_id="skill-copy",
        skill_version="1.0.0", model_name="qwen-max",
    )
    check("start → executing", t2.status == "executing")
    check("started_at 已置位", t2.started_at is not None)
    check("Trace 已开启并回写 trace_id", t2.trace_id is not None)
    trace = db.query(TaskTrace).filter(TaskTrace.id == t2.trace_id).first()
    check("Trace 行存在且 running", trace is not None and trace.status == "running")
    check("Trace 关联任务与类型",
          trace.task_id == t2.id and trace.trace_type == "ai_copywrite")
    check("Trace 记录 skill 与模型",
          trace.skill_id == "skill-copy" and trace.model_name == "qwen-max")

    t2 = svc.complete_task(
        t2.id, output_data={"text": "…"}, output_summary="文案已生成",
        tokens_used=800, cost=0.5, duration_ms=1200,
        skill_id="skill-copy", skill_version="1.0.0", model_name="qwen-max",
    )
    check("complete → done", t2.status == "done")
    check("finished_at 已置位", t2.finished_at is not None)
    check("output_json 已写入", "text" in (t2.output_json or ""))
    check("budget_used 累计成本", float(t2.budget_used or 0) == 0.5)
    db.expire_all()
    trace = db.query(TaskTrace).filter(TaskTrace.id == t2.trace_id).first()
    check("Trace 终态 success",
          trace.status == "success" and trace.success is True)
    check("Trace 回填 tokens/cost/duration",
          trace.tokens_used == 800 and float(trace.cost) == 0.5
          and trace.duration_ms == 1200)
    meter = (
        db.query(MeterEvent)
        .filter(MeterEvent.event_key == f"task:{t2.id}:ai_generation")
        .first()
    )
    check("ai_generation 计量已埋点", meter is not None)
    check("计量 token/cost 正确",
          meter is not None and meter.token_delta == 800 and meter.cost_cents == 50)
    check("计量关联任务", meter is not None and meter.source_ref_id == t2.id)
    rec = (
        db.query(EvolutionTaskRecord)
        .filter(EvolutionTaskRecord.tenant_id == tenant_a)
        .first()
    )
    check("终态钩子写 EvolutionTaskRecord(success)",
          rec is not None and rec.success is True)
    perf = (
        db.query(SkillPerformance)
        .filter(SkillPerformance.skill_id == "skill-copy")
        .first()
    )
    check("记分卡聚合 skill_performance",
          perf is not None and perf.total_invocations >= 1)
    try:
        svc.complete_task(t2.id, output_data={"again": 1})
        check("终态 done 不可再 complete", False)
    except InvalidTaskTransition:
        check("终态 done 不可再 complete", True)

    # ============ 4. 失败全链路 + 经验飞轮 ============
    print("== 4. 失败全链路：fail→Trace 失败→失败经验入库 ==")
    f1 = svc.create_task(
        tenant_id=tenant_a, task_type="ai_copywrite",
        idempotency_key="idem-f1", tenant=ok_tenant,
    )
    f1 = svc.start_task(f1.id, skill_id="skill-copy", skill_version="1.0.0")
    f1 = svc.fail_task(
        f1.id, error_code="E_LLM_TIMEOUT", error_message="上游超时",
        duration_ms=30000, skill_id="skill-copy",
    )
    check("fail → failed", f1.status == "failed")
    check("error_message 留痕", "E_LLM_TIMEOUT" in (f1.error_message or "")
          or "上游超时" in (f1.error_message or ""))
    ftrace = db.query(TaskTrace).filter(TaskTrace.id == f1.trace_id).first()
    check("Trace 终态 failed",
          ftrace is not None and ftrace.status == "failed"
          and ftrace.error_code == "E_LLM_TIMEOUT")
    exp = (
        db.query(ExperienceEntry)
        .filter(ExperienceEntry.pattern_type == "failure_pattern")
        .first()
    )
    check("失败经验快速入库（raw）",
          exp is not None and exp.stage == "raw" and exp.occurrence_count == 1)

    f2 = svc.create_task(
        tenant_id=tenant_a, task_type="ai_copywrite",
        idempotency_key="idem-f2", tenant=ok_tenant,
    )
    f2 = svc.start_task(f2.id, skill_id="skill-copy", skill_version="1.0.0")
    svc.fail_task(f2.id, error_code="E_LLM_TIMEOUT",
                  error_message="上游超时", skill_id="skill-copy")
    db.expire_all()
    exp = (
        db.query(ExperienceEntry)
        .filter(ExperienceEntry.pattern_type == "failure_pattern")
        .first()
    )
    check("同失败模式合并计数", exp.occurrence_count == 2,
          f"count={exp.occurrence_count}")
    f3 = svc.create_task(
        tenant_id=tenant_a, task_type="ai_copywrite",
        idempotency_key="idem-f3", tenant=ok_tenant,
    )
    f3 = svc.start_task(f3.id, skill_id="skill-copy", skill_version="1.0.0")
    svc.fail_task(f3.id, error_code="E_LLM_TIMEOUT",
                  error_message="上游超时", skill_id="skill-copy")
    db.expire_all()
    exp = (
        db.query(ExperienceEntry)
        .filter(ExperienceEntry.pattern_type == "failure_pattern")
        .first()
    )
    check("阈值晋级 validated（3 次）", exp.stage == "validated",
          f"stage={exp.stage}")

    # ============ 5. 状态机操作覆盖（pause/resume/review/retry/timeout/checkpoint） ============
    print("== 5. 状态机操作覆盖 ==")
    t5 = svc.create_task(
        tenant_id=tenant_c, task_type="content_publish",
        idempotency_key="cp-1",
    )
    t5 = svc.plan_task(t5.id)
    check("created→planning", t5.status == "planning")
    t5 = svc.start_task(t5.id)
    check("planning→executing", t5.status == "executing")
    t5 = svc.review_task(t5.id)
    check("executing→review", t5.status == "review")
    t5 = svc.pause_task(t5.id)
    check("review→paused", t5.status == "paused")
    t5 = svc.resume_task(t5.id)
    check("paused→executing（恢复）", t5.status == "executing")
    svc.save_checkpoint(t5.id, {"step": 3})
    check("checkpoint 保存并读取",
          svc.load_checkpoint(t5.id) == {"step": 3})
    t5 = svc.retry_task(t5.id)
    check("retrying 第 1 次合法", t5.status == "retrying" and t5.retry_count == 1)
    t5 = svc.resume_task(t5.id)
    t5 = svc.retry_task(t5.id)
    t5 = svc.resume_task(t5.id)
    t5 = svc.retry_task(t5.id)
    check("retrying 第 3 次合法（上限）", t5.retry_count == 3)
    t5 = svc.resume_task(t5.id)
    try:
        svc.retry_task(t5.id)
        check("第 4 次重试被拒（有界重试）", False)
    except InvalidTaskTransition as exc:
        check("第 4 次重试被拒（有界重试）", "wait_human" in str(exc))
    t5 = svc.cancel_task(t5.id)
    check("cancel → cancelled 且终态留痕",
          t5.status == "cancelled" and t5.finished_at is not None)
    t6 = svc.create_task(
        tenant_id=tenant_c, task_type="lead_outreach", idempotency_key="cp-2",
    )
    t6 = svc.start_task(t6.id)
    t6 = svc.timeout_task(t6.id)
    check("timeout → timeout 终态", t6.status == "timeout")
    try:
        svc.pause_task(t6.id)
        check("终态 timeout 不可 pause", False)
    except InvalidTaskTransition:
        check("终态 timeout 不可 pause", True)

    # ============ 6. 开关关：状态机可用 + 副作用跳过 ============
    print("== 6. 开关关：零副作用零回归 ==")
    _set_flag(False)
    t7 = svc.create_task(
        tenant_id=tenant_b, task_type="ai_content_generate",
        idempotency_key="idem-b2", tenant=ok_tenant,
    )
    t7 = svc.start_task(t7.id, skill_id="skill-x")
    t7 = svc.complete_task(
        t7.id, output_data={"ok": True}, tokens_used=500, cost=0.2,
        skill_id="skill-x",
    )
    check("开关关：状态机主链不受影响", t7.status == "done")
    check("开关关：不写 Trace", _fresh_count(TaskTrace, tenant_id=tenant_b) == 0)
    check("开关关：不埋计量",
          _fresh_count(MeterEvent, tenant_id=tenant_b) == 0)
    check("开关关：不写 Evolution 记录",
          _fresh_count(EvolutionTaskRecord, tenant_id=tenant_b) == 0)
    check("开关关：不聚合记分卡",
          db.query(SkillPerformance)
          .filter(SkillPerformance.skill_id == "skill-x").count() == 0)
    _set_flag(True)

    # ============ 7. 跨租户隔离 ============
    print("== 7. 跨租户隔离 ==")
    check("租户 B 取不到租户 A 任务",
          svc.get_task(t2.id, tenant_id=tenant_b) is None)
    try:
        svc.fail_task(t2.id, tenant_id=tenant_b)
        check("跨租户操作被拒（TaskNotFound）", False)
    except TaskNotFound:
        check("跨租户操作被拒（TaskNotFound）", True)

    # ============ 8. Model Gateway 成功路径计量旁路 ============
    print("== 8. Model Gateway ai_generation 计量旁路 ==")
    gw = ModelGateway()
    before = _fresh_count(MeterEvent, tenant_id=tenant_a)
    result = asyncio.run(gw.generate(
        "写一句产品文案", tenant_id=tenant_a, request_id="req-gw-1",
        task_id="task-gw-1",
    ))
    check("gateway 返回结构与 ai_engine 一致",
          result["content"] == "ok" and result["token_usage"] == 123)
    after = _fresh_count(MeterEvent, tenant_id=tenant_a)
    check("开关开：成功路径埋点 1 条", after - before == 1,
          f"delta={after - before}")
    gw_ev = (
        db.query(MeterEvent)
        .filter(MeterEvent.event_key == "model_gateway:req-gw-1")
        .first()
    )
    db.expire_all()
    gw_ev = (
        db.query(MeterEvent)
        .filter(MeterEvent.event_key == "model_gateway:req-gw-1")
        .first()
    )
    check("event_key 幂等键正确", gw_ev is not None)
    check("token_delta/cost_cents 正确",
          gw_ev is not None and gw_ev.token_delta == 123 and gw_ev.cost_cents == 5)
    check("模型名透传", gw_ev is not None and gw_ev.model_name == "general")
    asyncio.run(gw.generate(
        "再写一句", tenant_id=tenant_a, request_id="req-gw-1",
    ))
    check("重复 request_id 幂等去重",
          _fresh_count(MeterEvent, tenant_id=tenant_a) == after)
    asyncio.run(gw.generate(
        "换个 request", tenant_id=tenant_a, request_id="req-gw-2",
    ))
    check("新 request_id 新埋点",
          _fresh_count(MeterEvent, tenant_id=tenant_a) == after + 1)
    _set_flag(False)
    asyncio.run(gw.generate(
        "开关关调用", tenant_id=tenant_a, request_id="req-gw-3",
    ))
    check("开关关：不埋点",
          _fresh_count(MeterEvent, tenant_id=tenant_a) == after + 1)
    _set_flag(True)

    # ============ 9. 计量→token_ledger 对账收口 ============
    print("== 9. 计量→账本对账收口 ==")
    with DB_SHIM.SessionLocal() as s2:
        msvc = MeterEventService(s2)
        agg = msvc.aggregate_to_billing(tenant_id=tenant_a)
        check("租户 A 汇总 ai_generation",
              agg["token_events"] >= 1 and agg["token_delta"] >= 800,
              f"agg={agg}")
        r = msvc.reconcile(tenant_id=tenant_a)
        check("对账误差 0（error_free）", r["error_free"] is True,
              f"disc={r['discrepancies']}")
    tl = (
        db.query(TokenLedgerEntry)
        .filter(TokenLedgerEntry.tenant_id == tenant_a)
        .all()
    )
    check("token_ledger 已落扣减流水", len(tl) >= 1
          and any(t.delta < 0 for t in tl))
    db.expire_all()
    r_full = MeterEventService(db).reconcile(tenant_id=tenant_a)
    check("主会话对账复核 error_free", r_full["error_free"] is True,
          f"disc={r_full['discrepancies']}")

    # ============ 汇总 ============
    print(f"\n结果: {_passed} PASS / {_failed} FAIL")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
