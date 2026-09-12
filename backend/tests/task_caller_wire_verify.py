"""轮24-A DeerFlow→ai_tasks 影子双写 + 双记账防护 内存 SQLite 验证（不触碰真实 DB）。

用法：python -m tests.task_caller_wire_verify
依赖：sqlalchemy（已装）；无需 pytest / pydantic。

沿用 shim 模式。覆盖：
1) DeerflowTaskBridge 全生命周期影子双写（enqueue→started→finished 成功/失败）；
2) 开关关时完全旁路（零写入零回归）；
3) 幂等（重复 enqueue 同一 job 不重复建行）；
4) 跨租户安全（影子任务 tenant 隔离）；
5) 双记账防护闸：MODEL_CALL_LEDGER_AGGREGATE_ENABLED 默认关时
   aggregate_to_token_ledger 返回 0（即使有待汇总明细）；
6) deerflow_job_service 结构校验：三个桥接挂点在位（enqueue/run/finish）。
"""

import os
import sys
import types
import importlib.util
import json

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")

from sqlalchemy import String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class _Base(DeclarativeBase):
    pass


DB_SHIM.Base = _Base
DB_SHIM.UUID_TYPE = String(36)
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim（开关可切换）----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "task-caller-wire-verify-secret-2026"
    MODEL_GATEWAY_ENABLED = False
    EVOLUTION_TRACE_ENABLED = False
    TASK_CONTROL_ENABLED = False
    MODEL_CALL_LEDGER_AGGREGATE_ENABLED = False
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
    "app.services.ubrain",
    "app.services.model_gateway",
    "app.api",
    "app.api.v1",
    "app.api.v1.admin_bff",
):
    _new_dummy(_pkg)

_load_from_file(
    "app.api.v1.admin_bff.plan_catalog",
    os.path.join(_BACKEND, "app", "api", "v1", "admin_bff", "plan_catalog.py"),
)
_tenant_dummy = _new_dummy("app.models.tenant")


class _TenantType:
    pass


_tenant_dummy.Tenant = _TenantType

# ---- 模型（真实实现）----
for _name in ("ai_task", "trace", "evolution", "meter", "token_ledger",
              "finance_ledger", "deerflow_job"):
    _load_from_file(f"app.models.{_name}", os.path.join(_MODELS, f"{_name}.py"))

# ---- 服务（真实实现）----
_load_from_file(
    "app.services.billing.meter_event",
    os.path.join(_SERVICES, "billing", "meter_event.py"),
)
_load_from_file(
    "app.services.trace.trace_service",
    os.path.join(_SERVICES, "trace", "trace_service.py"),
)
_load_from_file(
    "app.services.trace.terminal_hook",
    os.path.join(_SERVICES, "trace", "terminal_hook.py"),
)
_load_from_file(
    "app.services.plan_gate_service",
    os.path.join(_SERVICES, "plan_gate_service.py"),
)
_tc_mod = _load_from_file(
    "app.services.tasks.task_control",
    os.path.join(_SERVICES, "tasks", "task_control.py"),
)
_bridge_mod = _load_from_file(
    "app.services.tasks.deerflow_bridge",
    os.path.join(_SERVICES, "tasks", "deerflow_bridge.py"),
)
_ledger_mod = _load_from_file(
    "app.services.model_gateway.ledger",
    os.path.join(_SERVICES, "model_gateway", "ledger.py"),
)

AiTask = _tc_mod.AiTask
TaskTrace = sys.modules["app.models.trace"].TaskTrace
EvolutionTaskRecord = sys.modules["app.models.evolution"].EvolutionTaskRecord
ExperienceEntry = sys.modules["app.models.evolution"].ExperienceEntry
DeerflowTaskBridge = _bridge_mod.DeerflowTaskBridge
idempotency_key_for = _bridge_mod.idempotency_key_for
aggregate_to_token_ledger = _ledger_mod.aggregate_to_token_ledger


# ---- 外部依赖表桩（FK 解析）----
class TenantShim(_Base):
    __tablename__ = "tenants"
    id = mapped_column(String(36), primary_key=True)


class UserShim(_Base):
    __tablename__ = "users"
    id = mapped_column(String(36), primary_key=True)


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


def _set_flag(name: str, on: bool) -> None:
    setattr(CFG_SHIM.settings, name, on)


def _db() -> Session:
    return sessionmaker(bind=_engine)()


class _FakeJob:
    """DeerflowJob 形状桩（避免加载 deerflow_job_service 重型依赖链）。"""

    def __init__(self, job_id, tenant_id, intent, payload=None,
                 status="queued", result=None, error=None, created_by=None):
        self.id = job_id
        self.tenant_id = tenant_id
        self.intent = intent
        self.payload_json = json.dumps(payload or {}, ensure_ascii=False)
        self.result_json = json.dumps(result, ensure_ascii=False) if result else None
        self.error_message = error
        self.status = status
        self.created_by = created_by


def main() -> int:
    tenant_a = "tenant-a-0001"
    tenant_b = "tenant-b-0002"

    # ============ 1. 开关关：桥完全旁路 ============
    print("== 1. 开关关：桥完全旁路（零回归） ==")
    db = _db()
    bridge = DeerflowTaskBridge(db)
    job1 = _FakeJob("job-1", tenant_a, "lead_content_pack",
                    payload={"message": "写内容"})
    bridge.on_job_enqueued(job1)
    bridge.on_job_started(job1)
    bridge.on_job_finished(job1, success=True)
    check("开关关：ai_tasks 零写入", db.query(AiTask).count() == 0)
    check("开关关：Trace 零写入", db.query(TaskTrace).count() == 0)
    _set_flag("TASK_CONTROL_ENABLED", True)

    # ============ 2. 开关开：全生命周期影子双写 ============
    print("== 2. 全生命周期影子双写 ==")
    job2 = _FakeJob("job-2", tenant_a, "market_research",
                    payload={"message": "蓝海研究"}, created_by="user-1")
    bridge.on_job_enqueued(job2)
    shadow = (
        db.query(AiTask)
        .filter(AiTask.idempotency_key == idempotency_key_for("job-2"))
        .first()
    )
    check("enqueue 影子建任务", shadow is not None)
    check("task_type 映射 intent", shadow.task_type == "deerflow_market_research")
    check("状态 created + source=deerflow",
          shadow.status == "created" and shadow.source == "deerflow")
    check("input_json 承载 payload", "蓝海研究" in (shadow.input_json or ""))
    check("created_by 透传", shadow.created_by == "user-1")

    job2.status = "running"
    bridge.on_job_started(job2)
    db.expire_all()
    shadow = (
        db.query(AiTask)
        .filter(AiTask.idempotency_key == idempotency_key_for("job-2"))
        .first()
    )
    check("started 影子转 executing", shadow.status == "executing")
    check("start 开 Trace 并回写", shadow.trace_id is not None)
    trace = db.query(TaskTrace).filter(TaskTrace.id == shadow.trace_id).first()
    check("Trace running 且类型正确",
          trace is not None and trace.status == "running"
          and trace.trace_type == "deerflow_market_research")

    job2.status = "success"
    job2.result_json = json.dumps(
        {"insight": "机会点", "cms_draft_count": 3}, ensure_ascii=False
    )
    bridge.on_job_finished(job2, success=True)
    db.expire_all()
    shadow = (
        db.query(AiTask)
        .filter(AiTask.idempotency_key == idempotency_key_for("job-2"))
        .first()
    )
    check("成功影子转 done", shadow.status == "done")
    check("output_json 承载 result", "机会点" in (shadow.output_json or ""))
    trace = db.query(TaskTrace).filter(TaskTrace.id == shadow.trace_id).first()
    check("Trace 终态 success", trace.status == "success")
    rec = (
        db.query(EvolutionTaskRecord)
        .filter(EvolutionTaskRecord.tenant_id == tenant_a)
        .first()
    )
    check("终态钩子写 EvolutionTaskRecord", rec is not None and rec.success is True)
    check("executor_type=workflow 透传", rec.executor_type == "workflow"
          and rec.executor_id == "deerflow:market_research")

    # ============ 3. 失败链路 + 失败经验 ============
    print("== 3. 失败链路影子同步 ==")
    job3 = _FakeJob("job-3", tenant_a, "osint_check",
                    payload={"target": "example.com"})
    bridge.on_job_enqueued(job3)
    job3.status = "running"
    bridge.on_job_started(job3)
    job3.status = "failed"
    job3.error_message = "上游 OSINT 服务超时"
    bridge.on_job_finished(job3, success=False)
    db.expire_all()
    shadow3 = (
        db.query(AiTask)
        .filter(AiTask.idempotency_key == idempotency_key_for("job-3"))
        .first()
    )
    check("失败影子转 failed", shadow3.status == "failed")
    check("error_message 留痕", "OSINT" in (shadow3.error_message or ""))
    exp = (
        db.query(ExperienceEntry)
        .filter(ExperienceEntry.pattern_type == "failure_pattern")
        .first()
    )
    check("失败经验入库", exp is not None and exp.stage == "raw")

    # ============ 4. 幂等（重复 enqueue 不重复建行） ============
    print("== 4. 幂等 ==")
    bridge.on_job_enqueued(job2)
    check("重复 enqueue 不重复建行",
          db.query(AiTask)
          .filter(AiTask.idempotency_key == idempotency_key_for("job-2")).count() == 1)
    check("重复 enqueue 不改终态",
          db.query(AiTask)
          .filter(AiTask.idempotency_key == idempotency_key_for("job-2"))
          .first().status == "done")

    # ============ 5. 跨租户安全 ============
    print("== 5. 跨租户安全 ==")
    job_b = _FakeJob("job-2", tenant_b, "market_research")  # 同 job.id 不同租户
    bridge.on_job_enqueued(job_b)
    check("不同租户同 job.id 各自建行",
          db.query(AiTask)
          .filter(AiTask.idempotency_key == idempotency_key_for("job-2")).count() == 2)
    check("租户隔离正确",
          db.query(AiTask)
          .filter(AiTask.idempotency_key == idempotency_key_for("job-2"),
                  AiTask.tenant_id == tenant_b).first().status == "created")

    # ============ 6. 双记账防护闸 ============
    print("== 6. 双记账防护闸（MODEL_CALL_LEDGER_AGGREGATE_ENABLED） ==")
    with DB_SHIM.SessionLocal() as s:
        s.execute(text(
            "CREATE TABLE IF NOT EXISTS model_call_ledger ("
            "id VARCHAR(36) PRIMARY KEY, tenant_id VARCHAR(36), task_id VARCHAR(36),"
            "provider VARCHAR(100), model_name VARCHAR(100), capability_tag VARCHAR(50),"
            "prompt_tokens INTEGER, completion_tokens INTEGER, total_tokens INTEGER,"
            "cost_usd FLOAT, latency_ms INTEGER, status VARCHAR(20),"
            "error_message TEXT, called_at TIMESTAMP, request_id VARCHAR(64),"
            "metadata_json TEXT)"
        ))
        s.execute(text(
            "INSERT INTO model_call_ledger (id, tenant_id, total_tokens, status,"
            "called_at) VALUES ('mcl-1', :t, 500, 'success', CURRENT_TIMESTAMP)"
        ), {"t": tenant_a})
        s.commit()
    check("防护闸默认关：有明细也返回 0",
          aggregate_to_token_ledger(tenant_a) == 0)
    check("防护闸默认关：token_ledger 零写入",
          db.query(sys.modules["app.models.token_ledger"].TokenLedgerEntry)
          .count() == 0)
    _set_flag("MODEL_CALL_LEDGER_AGGREGATE_ENABLED", True)
    n = aggregate_to_token_ledger(tenant_a)
    check("显式开启后正常聚合", n == 1, f"n={n}")
    _set_flag("MODEL_CALL_LEDGER_AGGREGATE_ENABLED", False)

    # ============ 7. deerflow_job_service 桥接挂点结构校验 ============
    print("== 7. deerflow_job_service 桥接挂点结构校验 ==")
    svc_path = os.path.join(_SERVICES, "ubrain", "deerflow_job_service.py")
    with open(svc_path, encoding="utf-8") as f:
        src = f.read()
    check("enqueue 挂点在位", "_bridge(db).on_job_enqueued(job)" in src)
    check("run 挂点在位", "_bridge(db).on_job_started(job)" in src)
    check("finish 挂点在位（success 判定）",
          "_bridge(db).on_job_finished(job, success=(job.status == \"success\"))" in src)
    check("挂点均在 commit 之后（先落库再双写）",
          src.index("_bridge(db).on_job_enqueued") > src.index("db.commit()")
          if "_bridge(db).on_job_enqueued" in src else False)
    # 桥内 best-effort：模拟 find_by_idempotency 抛异常不外泄
    print("== 8. 桥 best-effort：内部异常不外泄 ==")

    class _BoomControl:
        def __getattr__(self, name):
            raise RuntimeError("boom")

    broken = DeerflowTaskBridge(db)
    broken._control = lambda: _BoomControl()
    try:
        broken.on_job_enqueued(job2)
        broken.on_job_started(job2)
        broken.on_job_finished(job2, success=True)
        check("桥内异常全吞不外泄", True)
    except Exception as exc:  # noqa: BLE001
        check("桥内异常全吞不外泄", False, f"leaked={exc}")

    # ============ 汇总 ============
    print(f"\n结果: {_passed} PASS / {_failed} FAIL")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
