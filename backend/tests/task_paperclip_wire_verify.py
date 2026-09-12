"""轮24-B Paperclip→ai_tasks 影子双写 + deerflow 去重裁决 内存 SQLite 验证。

用法：python -m tests.task_paperclip_wire_verify
依赖：sqlalchemy（已装）；无需 pytest / pydantic。

沿用 shim 模式。覆盖：
1) 开关关：paperclip 桥完全旁路（零写入零回归）；
2) 全生命周期影子双写：created→executing→done（tenant 经 company 解析、
   task_type/source/priority 映射、Trace executor_type=agent、终态钩子）；
3) 失败链路：result_json.error 留痕 + 失败经验入库；
4) 幂等与影子缺失补建（running 时影子缺失先补建再启动）；
5) 租户解析降级（company 查不到用 company_id）；
6) deerflow 去重裁决：payload.context.paperclip=True 的 job 不再影子（一工作一记录）；
7) 接线挂点结构校验（orchestrator 两点 + heartbeat_engine 三点）；
8) 桥 best-effort：内部异常不外泄。
"""

import json
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

# ---- 预置 app.core.config shim ----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "task-paperclip-wire-verify-secret-2026"
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
    "app.services.paperclip",
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
              "finance_ledger", "deerflow_job", "paperclip"):
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
_pc_bridge_mod = _load_from_file(
    "app.services.tasks.paperclip_bridge",
    os.path.join(_SERVICES, "tasks", "paperclip_bridge.py"),
)
_df_bridge_mod = _load_from_file(
    "app.services.tasks.deerflow_bridge",
    os.path.join(_SERVICES, "tasks", "deerflow_bridge.py"),
)

AiTask = _tc_mod.AiTask
TaskTrace = sys.modules["app.models.trace"].TaskTrace
EvolutionTaskRecord = sys.modules["app.models.evolution"].EvolutionTaskRecord
ExperienceEntry = sys.modules["app.models.evolution"].ExperienceEntry
PaperclipTaskBridge = _pc_bridge_mod.PaperclipTaskBridge
pc_idempotency_key_for = _pc_bridge_mod.idempotency_key_for
pc_resolve_tenant_id = _pc_bridge_mod.resolve_tenant_id
DeerflowTaskBridge = _df_bridge_mod.DeerflowTaskBridge
df_idempotency_key_for = _df_bridge_mod.idempotency_key_for
PaperclipCompany = sys.modules["app.models.paperclip"].PaperclipCompany


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


def _set_flag(on: bool) -> None:
    CFG_SHIM.settings.TASK_CONTROL_ENABLED = on


def _db() -> Session:
    return sessionmaker(bind=_engine)()


def _shadow(db: Session, task_id: str):
    return (
        db.query(AiTask)
        .filter(AiTask.idempotency_key == pc_idempotency_key_for(task_id))
        .first()
    )


class _FakeTask:
    """PaperclipTask 形状桩。"""

    def __init__(self, task_id, company_id, title="开发信任务", intent="outreach_letter_pack",
                 description="", goal_id=None, agent_id=None, priority=0,
                 status="queued", result=None):
        self.id = task_id
        self.company_id = company_id
        self.goal_id = goal_id
        self.assigned_agent_id = agent_id
        self.title = title
        self.description = description
        self.intent = intent
        self.priority = priority
        self.status = status
        self.result_json = json.dumps(result, ensure_ascii=False) if result else None


def main() -> int:
    tenant_a = "tenant-a-0001"
    company_a = "company-a-0001"
    company_orphan = "company-no-row"

    db = _db()
    db.add(PaperclipCompany(id=company_a, tenant_id=tenant_a, name="优丁建材"))
    db.commit()

    bridge = PaperclipTaskBridge(db)

    # ============ 1. 开关关：桥完全旁路 ============
    print("== 1. 开关关：桥完全旁路 ==")
    t0 = _FakeTask("pt-0", company_a)
    bridge.on_task_created(t0)
    bridge.on_task_running(t0)
    bridge.on_task_finished(t0, success=True)
    check("开关关：ai_tasks 零写入", db.query(AiTask).count() == 0)
    check("开关关：Trace 零写入", db.query(TaskTrace).count() == 0)
    _set_flag(True)

    # ============ 2. 全生命周期影子双写 ============
    print("== 2. 全生命周期影子双写 ==")
    agent_id = "agent-0001"
    t1 = _FakeTask("pt-1", company_a, intent="outreach_letter_pack",
                   agent_id=agent_id, priority=-1, description="给买家写开发信")
    bridge.on_task_created(t1)
    s1 = _shadow(db, "pt-1")
    check("create 影子建任务", s1 is not None)
    check("task_type 映射 intent", s1.task_type == "paperclip_outreach_letter_pack")
    check("source=paperclip + created 态",
          s1.source == "paperclip" and s1.status == "created")
    check("租户经 company 解析", s1.tenant_id == tenant_a)
    check("priority 映射（-1 → 2）", s1.priority == 2, f"p={s1.priority}")
    check("input_json 承载 title/description",
          "开发信" in (s1.input_json or "") and "买家" in (s1.input_json or ""))

    t1.status = "running"
    bridge.on_task_running(t1)
    db.expire_all()
    s1 = _shadow(db, "pt-1")
    check("running 影子转 executing", s1.status == "executing")
    check("start 开 Trace 并回写", s1.trace_id is not None)
    trace = db.query(TaskTrace).filter(TaskTrace.id == s1.trace_id).first()
    check("Trace running 且类型正确",
          trace is not None and trace.status == "running"
          and trace.trace_type == "paperclip_outreach_letter_pack")

    t1.status = "success"
    t1.result_json = json.dumps({"status": "success", "letters": 3}, ensure_ascii=False)
    bridge.on_task_finished(t1, success=True)
    db.expire_all()
    s1 = _shadow(db, "pt-1")
    check("成功影子转 done", s1.status == "done")
    check("output_json 承载 result", "letters" in (s1.output_json or ""))
    trace = db.query(TaskTrace).filter(TaskTrace.id == s1.trace_id).first()
    check("Trace 终态 success", trace.status == "success")
    rec = (
        db.query(EvolutionTaskRecord)
        .filter(EvolutionTaskRecord.tenant_id == tenant_a)
        .first()
    )
    check("终态钩子记录 agent 归属",
          rec is not None and rec.executor_type == "agent"
          and rec.executor_id == f"paperclip:{agent_id}")

    # ============ 3. 失败链路 ============
    print("== 3. 失败链路影子同步 ==")
    t2 = _FakeTask("pt-2", company_a, intent="find_buyers",
                   result={"error": "Accio API 超时"})
    bridge.on_task_created(t2)
    t2.status = "running"
    bridge.on_task_running(t2)
    t2.status = "failed"
    bridge.on_task_finished(t2, success=False)
    db.expire_all()
    s2 = _shadow(db, "pt-2")
    check("失败影子转 failed", s2.status == "failed")
    check("error_message 从 result_json 提取", "Accio" in (s2.error_message or ""))
    exp = (
        db.query(ExperienceEntry)
        .filter(ExperienceEntry.pattern_type == "failure_pattern")
        .first()
    )
    check("失败经验入库", exp is not None and exp.stage == "raw")

    # ============ 4. 幂等 + 影子缺失补建 ============
    print("== 4. 幂等与补建 ==")
    bridge.on_task_created(t1)
    check("重复 create 不重复建行",
          db.query(AiTask)
          .filter(AiTask.idempotency_key == pc_idempotency_key_for("pt-1")).count() == 1)
    t3 = _FakeTask("pt-3", company_a, intent="market_research")
    # 开关中途才开的场景：直接 running（无 create 影子）→ 补建再启动
    t3.status = "running"
    bridge.on_task_running(t3)
    db.expire_all()
    s3 = _shadow(db, "pt-3")
    check("影子缺失自动补建并启动",
          s3 is not None and s3.status == "executing")

    # ============ 5. 租户解析降级 ============
    print("== 5. 租户解析降级 ==")
    check("company 无行 → 降级用 company_id",
          pc_resolve_tenant_id(db, company_orphan) == company_orphan)
    t4 = _FakeTask("pt-4", company_orphan, intent="geo_content_matrix")
    bridge.on_task_created(t4)
    s4 = _shadow(db, "pt-4")
    check("降级租户影子可建", s4 is not None and s4.tenant_id == company_orphan)

    # ============ 6. deerflow 去重裁决 ============
    print("== 6. deerflow 去重裁决（paperclip 代执行跳过影子） ==")
    df_bridge = DeerflowTaskBridge(db)
    before = db.query(AiTask).count()
    job_pc = SimpleNamespace(
        id="job-pc-1", tenant_id=tenant_a, intent="lead_content_pack",
        payload_json=json.dumps({
            "message": "写内容",
            "context": {"paperclip": True, "task_id": "pt-1"},
        }, ensure_ascii=False),
        created_by="paperclip_agent:agent-0001",
        status="queued", result_json=None, error_message=None,
    )
    df_bridge.on_job_enqueued(job_pc)
    check("paperclip 代执行 job 不建 deerflow 影子",
          db.query(AiTask).count() == before)
    check("deerflow 幂等键无残留行",
        db.query(AiTask)
        .filter(AiTask.idempotency_key == df_idempotency_key_for("job-pc-1")).count() == 0)
    job_direct = SimpleNamespace(
        id="job-direct-1", tenant_id=tenant_a, intent="market_research",
        payload_json=json.dumps({"message": "研究"}, ensure_ascii=False),
        created_by="user-1",
        status="queued", result_json=None, error_message=None,
    )
    df_bridge.on_job_enqueued(job_direct)
    check("普通 job 照常建 deerflow 影子",
          db.query(AiTask)
          .filter(AiTask.idempotency_key == df_idempotency_key_for("job-direct-1"))
          .count() == 1)

    # ============ 7. 接线挂点结构校验 ============
    print("== 7. 接线挂点结构校验 ==")
    with open(os.path.join(_SERVICES, "paperclip", "orchestrator.py"),
              encoding="utf-8") as f:
        orch_src = f.read()
    with open(os.path.join(_SERVICES, "paperclip", "heartbeat_engine.py"),
              encoding="utf-8") as f:
        hb_src = f.read()
    check("orchestrator create_task 挂点在位",
          "_bridge(db).on_task_created(task)" in orch_src)
    check("orchestrator 批量建任务挂点在位",
          "for t in _batch_tasks:\n        _bridge(db).on_task_created(t)" in orch_src)
    check("heartbeat running 挂点在位", "_bridge(db).on_task_running(task)" in hb_src)
    check("heartbeat success 挂点在位",
          '_bridge(db).on_task_finished(task, success=True)' in hb_src)
    check("heartbeat failed 挂点在位",
          '_bridge(db).on_task_finished(task, success=False)' in hb_src)
    check("挂点均在 commit 之后（先落库再双写）",
          hb_src.index("_bridge(db).on_task_running")
          > hb_src.index('task.status = "running"')
          and hb_src.index("_bridge(db).on_task_finished(task, success=True)")
          > hb_src.index('task.status = "success"'))

    # ============ 8. 桥 best-effort：内部异常不外泄 ============
    print("== 8. 桥 best-effort：内部异常不外泄 ==")

    class _BoomControl:
        def __getattr__(self, name):
            raise RuntimeError("boom")

    broken = PaperclipTaskBridge(db)
    broken._control = lambda: _BoomControl()
    try:
        broken.on_task_created(t1)
        broken.on_task_running(t1)
        broken.on_task_finished(t1, success=True)
        check("桥内异常全吞不外泄", True)
    except Exception as exc:  # noqa: BLE001
        check("桥内异常全吞不外泄", False, f"leaked={exc}")

    # ============ 汇总 ============
    print(f"\n结果: {_passed} PASS / {_failed} FAIL")
    return 1 if _failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
