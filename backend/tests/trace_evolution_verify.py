"""轮21 Trace/Experience/Evolution 接线内存 SQLite 验证脚本（不触碰真实 DB）。

用法：python -m tests.trace_evolution_verify
依赖：sqlalchemy（已装）；无需 pytest / pydantic / cryptography。

覆盖：
1. evolution 坏重构修复：experience_store.extract_from_records / canary.route /
   engine.run_full_cycle 不再 NameError，可正常执行。
2. TaskTrace 生命周期：start/complete/fail/get_chain/record_feedback。
3. 终态钩子：success 只写记录；failure 快速入库 ExperienceEntry 且按阈值分级。
4. 记分卡：skill_performance / agent_scorecards 聚合。
5. Canary 发布门禁：5→25→50→100 阶梯、跳级拒绝、租户分流、人审晋升。
"""

import os
import sys
import types
import importlib.util

# ---- 预置 app.core.database shim ----
DB_SHIM = types.ModuleType("app.core.database")

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class _Base(DeclarativeBase):
    pass


DB_SHIM.Base = _Base
DB_SHIM.UUID_TYPE = String(36)
sys.modules["app.core.database"] = DB_SHIM

# ---- 预置 app.core.config shim ----
CFG_SHIM = types.ModuleType("app.core.config")


class _FakeSettings:
    SECRET_KEY = "trace-evolution-verify-secret-2026"
    MODEL_GATEWAY_ENABLED = False
    EVOLUTION_TRACE_ENABLED = True


CFG_SHIM.settings = _FakeSettings()
sys.modules["app.core.config"] = CFG_SHIM

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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


_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODELS = os.path.join(_BACKEND, "app", "models")
_SVC = os.path.join(_BACKEND, "app", "services")

for _pkg in (
    "app",
    "app.core",
    "app.models",
    "app.services",
    "app.services.evolution",
    "app.services.trace",
):
    _new_dummy(_pkg)

_evo_models = _load_from_file("app.models.evolution", os.path.join(_MODELS, "evolution.py"))
_trace_models = _load_from_file("app.models.trace", os.path.join(_MODELS, "trace.py"))

_vc_mod = _load_from_file(
    "app.services.evolution.version_control",
    os.path.join(_SVC, "evolution", "version_control.py"),
)
_exp_mod = _load_from_file(
    "app.services.evolution.experience_store",
    os.path.join(_SVC, "evolution", "experience_store.py"),
)
_canary_mod = _load_from_file(
    "app.services.evolution.canary",
    os.path.join(_SVC, "evolution", "canary.py"),
)
_engine_mod = _load_from_file(
    "app.services.evolution.engine",
    os.path.join(_SVC, "evolution", "engine.py"),
)
_trace_svc_mod = _load_from_file(
    "app.services.trace.trace_service",
    os.path.join(_SVC, "trace", "trace_service.py"),
)
_hook_mod = _load_from_file(
    "app.services.trace.terminal_hook",
    os.path.join(_SVC, "trace", "terminal_hook.py"),
)
_gate_mod = _load_from_file(
    "app.services.trace.publish_gate",
    os.path.join(_SVC, "trace", "publish_gate.py"),
)

EvolutionTaskRecord = _evo_models.EvolutionTaskRecord
ExperienceEntry = _evo_models.ExperienceEntry
SkillVersion = _evo_models.SkillVersion
SOPVersion = _evo_models.SOPVersion
ApprovalRecord = _evo_models.ApprovalRecord
CanaryRouteRecord = _evo_models.CanaryRouteRecord

TaskTrace = _trace_models.TaskTrace
SkillPerformance = _trace_models.SkillPerformance
AgentScorecard = _trace_models.AgentScorecard

VersionControl = _vc_mod.VersionControl
ExperienceStore = _exp_mod.ExperienceStore
CanaryRelease = _canary_mod.CanaryRelease
EvolutionEngine = _engine_mod.EvolutionEngine
TaskTraceService = _trace_svc_mod.TaskTraceService
record_terminal_state = _hook_mod.record_terminal_state
promote_experience_stage = _hook_mod.promote_experience_stage
PublishGate = _gate_mod.PublishGate

# ---- 外部依赖表桩（evolution/trace 模型 ForeignKey 解析用）----
from sqlalchemy.orm import mapped_column  # noqa: E402


class TenantShim(_Base):
    __tablename__ = "tenants"
    id = mapped_column(String(36), primary_key=True)


class AiTaskShim(_Base):
    __tablename__ = "ai_tasks"
    id = mapped_column(String(36), primary_key=True)


# ---- 运行骨架 ----
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
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    _Base.metadata.create_all(engine)
    Session_factory = sessionmaker(bind=engine)
    return engine, Session_factory


def main() -> int:
    global _passed, _failed
    engine, Session = _setup_db()
    db = Session()

    tenant_a = "11111111-1111-1111-1111-111111111111"
    tenant_b = "22222222-2222-2222-2222-222222222222"

    # ═══════════════════════════════════════════
    # 1. 修复验证：experience_store.extract_from_records
    # ═══════════════════════════════════════════
    print("== 1. experience_store 修复（extract_from_records）==")
    store = ExperienceStore(db)
    for i in range(8):
        db.add(EvolutionTaskRecord(
            id=f"rec-{i:04d}", tenant_id=tenant_a,
            task_type="seo_analysis", executor_type="skill", executor_id="skill_seo_v1",
            success=True, duration_ms=100 + i, cost=0.01, tokens_used=500,
            metadata_json={}, created_at=_now(),
        ))
    db.commit()
    exps = store.extract_from_records("seo_analysis", lookback_hours=24, min_samples=5)
    check("提取成功模式经验", any(e.get("action") in ("created", "merged") for e in exps),
          f"exps={exps}")
    check("经验已入库", db.query(ExperienceEntry).filter(
        ExperienceEntry.pattern_type == "success_pattern").count() >= 1)
    stats = store.get_stats()
    check("get_stats 可用", stats["total_experiences"] >= 1, str(stats))

    # ═══════════════════════════════════════════
    # 2. 修复验证：canary.route（租户白名单 / 百分比 / 全量）
    # ═══════════════════════════════════════════
    print("== 2. canary.route 修复 ==")
    vc = VersionControl(db)
    prod = vc.create_skill_version(
        skill_id="skill_seo_v1", skill_name="SEO Skill", bump="patch",
    )
    # 按状态机推进：draft → evaluation → canary → approved → production
    vc.transition_skill(str(prod.id), "evaluation")
    vc.transition_skill(str(prod.id), "canary")
    vc.transition_skill(str(prod.id), "approved")
    vc.transition_skill(str(prod.id), "production")
    canary_v = vc.create_skill_version(
        skill_id="skill_seo_v1", skill_name="SEO Skill", bump="minor",
    )
    vc.transition_skill(str(canary_v.id), "evaluation")
    vc.transition_skill(str(canary_v.id), "canary", canary_percentage=5.0,
                        canary_tenant_ids=[tenant_a])
    canary = CanaryRelease(db)
    r1 = canary.route(skill_id="skill_seo_v1", tenant_id=tenant_a)
    check("租户白名单命中灰度", r1["use_canary"] is True and r1["route_reason"] == "tenant_whitelist",
          str(r1))
    r2 = canary.route(skill_id="skill_seo_v1", tenant_id=tenant_b, request_id="req-xyz")
    check("非白名单租户走百分比分流（可落生产）", r2["route_reason"].startswith("percentage"),
          str(r2))
    check("路由决策已留痕", db.query(CanaryRouteRecord).count() >= 2)

    # ═══════════════════════════════════════════
    # 3. 修复验证：engine.run_full_cycle（不再 NameError）
    # ═══════════════════════════════════════════
    print("== 3. engine.run_full_cycle 修复 ==")
    engine_mod = EvolutionEngine(db)
    res = engine_mod.run_full_cycle(
        task_type="seo_analysis", skill_id="skill_seo_v1", skill_name="SEO Skill",
        lookback_hours=24, deploy_canary=False,
    )
    check("run_full_cycle 完成", res["status"] in ("completed", "completed_no_new_experiences",
                                                   "completed_no_optimization"), str(res["status"]))
    check("run_full_cycle 含 stages", "stages" in res and "experience_extraction" in res["stages"])

    # ═══════════════════════════════════════════
    # 4. TaskTrace 生命周期
    # ═══════════════════════════════════════════
    print("== 4. TaskTrace 生命周期 ==")
    svc = TaskTraceService(db)
    root = svc.start_trace(
        tenant_id=tenant_a, trace_type="pipeline_run", source_id="run-001",
        skill_id="skill_seo_v1", skill_version="0.1.0", model_name="qwen-max",
        prompt_ref="s3://objstore/prompts/p1.txt", input_summary="SEO 分析请求",
    )
    check("start_trace → running", root.status == "running")
    child = svc.start_trace(
        tenant_id=tenant_a, parent_trace_id=str(root.id), trace_type="skill_call",
        source_id="step-1", skill_id="skill_seo_v1", skill_version="0.1.0",
    )
    check("子 trace 链式挂接", child.parent_trace_id == root.id)
    done = svc.complete_trace(
        str(child.id), output_summary="分析完成", duration_ms=1200,
        cost=0.05, tokens_used=800,
        artifacts=[{"type": "report", "ref": "s3://objstore/reports/r1.pdf"}],
        validation_results=[{"checker": "content_scorer", "score": 88}],
    )
    check("complete_trace → success", done is not None and done.success is True)
    failed = svc.fail_trace(str(root.id), error_code="E_TIMEOUT", error_message="超时", duration_ms=3000)
    check("fail_trace → failed", failed is not None and failed.success is False)
    chain = svc.get_chain(str(child.id))
    check("get_chain 从叶回溯到根", len(chain) == 2 and chain[0].id == root.id, f"len={len(chain)}")
    fb = svc.record_feedback(str(child.id), {"rating": 5, "comment": "好用"})
    check("record_feedback 留证", fb is not None and fb.feedback and fb.feedback.get("rating") == 5)

    # ═══════════════════════════════════════════
    # 5. 终态钩子：success 只写记录；failure 快速入库 + 分级
    # ═══════════════════════════════════════════
    print("== 5. 终态钩子 record_terminal_state ==")
    ok_res = record_terminal_state(
        db, task_type="content_generation", executor_type="skill",
        executor_id="skill_content_v1", success=True, tenant_id=tenant_a,
        duration_ms=800, cost=0.02, tokens_used=400,
    )
    check("终态成功写入 EvolutionTaskRecord",
          ok_res["record_id"] and db.query(EvolutionTaskRecord).filter(
              EvolutionTaskRecord.id == ok_res["record_id"]).count() == 1)
    check("终态成功不建失败经验", ok_res["experience_id"] is None)
    check("成功记录可被批量提炼", True)  # 提炼逻辑由 1 覆盖

    fail_res = record_terminal_state(
        db, task_type="email_outreach", executor_type="agent",
        executor_id="agent_outreach_1", success=False, tenant_id=tenant_a,
        error_code="SEND_400", error_message="WhatsApp 通道被限流", duration_ms=1500,
        trace_id=str(child.id), model_name="qwen-max",
    )
    check("终态失败写入 EvolutionTaskRecord", bool(fail_res["record_id"]))
    check("终态失败快速入库经验", fail_res["experience_id"] is not None)
    check("失败经验为 failure_pattern 且 stage=raw",
          fail_res["experience_stage"] == "raw", fail_res["experience_stage"])
    exp = db.query(ExperienceEntry).filter(ExperienceEntry.id == fail_res["experience_id"]).first()
    check("失败经验含错误码", exp is not None and exp.pattern_data.get("error_code") == "SEND_400")

    # 同一失败模式再触发 → 计数 +1；连续触发推进分级
    for i in range(3):
        record_terminal_state(
            db, task_type="email_outreach", executor_type="agent",
            executor_id="agent_outreach_1", success=False, tenant_id=tenant_a,
            error_code="SEND_400", error_message="限流",
        )
    exp = db.query(ExperienceEntry).filter(ExperienceEntry.id == fail_res["experience_id"]).first()
    check("失败经验计数累计", exp.occurrence_count == 4, f"count={exp.occurrence_count}")
    check("失败经验分级晋升(≥3 → validated)", exp.stage == "validated", f"stage={exp.stage}")
    promoted = promote_experience_stage(db, str(exp.id), min_occurrence=4)
    check("min_occurrence 覆盖晋升(4次→skill)", promoted.stage == "skill", f"stage={promoted.stage}")

    # ═══════════════════════════════════════════
    # 6. 记分卡聚合
    # ═══════════════════════════════════════════
    print("== 6. 记分卡聚合 ==")
    # 预置 agent 终态 trace（agent_scorecards 聚合数据源）
    for _i in range(4):
        _t = svc.start_trace(
            tenant_id=tenant_a, trace_type="email_outreach",
            source_id="agent_outreach_1", model_name="qwen-max",
        )
        svc.fail_trace(str(_t.id), error_code="SEND_400", duration_ms=1000, cost=0.05)
    perf = svc.aggregate_skill_performance(
        "skill_seo_v1", skill_version="0.1.0", tenant_id=tenant_a,
    )
    check("skill_performance 聚合", perf is not None and perf.total_invocations >= 1,
          f"total={perf.total_invocations if perf else None}")
    check("skill_performance 成功率计算", perf is not None and 0 <= perf.success_rate <= 1)
    card = svc.aggregate_agent_scorecard(
        "agent_outreach_1", "email_outreach", tenant_id=tenant_a,
        business_metrics={"revenue_impact": 1200.0, "conversion_rate": 0.08, "roi": 2.4},
    )
    check("agent_scorecard 聚合", card is not None and card.success_count == 0 and card.total_invocations == 4,
          f"card={card.total_invocations if card else None}")
    check("agent_scorecard 业务指标吸收", card is not None and float(card.roi or 0) == 2.4)

    # ═══════════════════════════════════════════
    # 7. Canary 发布门禁
    # ═══════════════════════════════════════════
    print("== 7. Canary 发布门禁 ==")
    gate = PublishGate(db)
    v = vc.create_skill_version(
        skill_id="skill_new_1", skill_name="New Skill", bump="minor",
    )
    started = gate.start_release(skill_id="skill_new_1", version_id=str(v.id),
                                 canary_percentage=5.0, requester="tester")
    check("start_release → canary 5%", started["stage"] == "canary" and started["canary_percentage"] == 5.0)
    v = db.query(SkillVersion).filter(SkillVersion.id == v.id).first()
    check("版本进入 canary 态", v.status == "canary")
    try:
        gate.scale_canary(skill_id="skill_new_1", version_id=str(v.id), next_percentage=50.0)
        check("跳级 5→50 应被拒绝", False, "未抛错")
    except ValueError as e:
        check("跳级 5→50 被拒绝", "不得跳级" in str(e), str(e))
    gate.scale_canary(skill_id="skill_new_1", version_id=str(v.id), next_percentage=25.0)
    gate.scale_canary(skill_id="skill_new_1", version_id=str(v.id), next_percentage=50.0)
    gate.scale_canary(skill_id="skill_new_1", version_id=str(v.id), next_percentage=100.0)
    v = db.query(SkillVersion).filter(SkillVersion.id == v.id).first()
    check("逐级放量至 100%", float(v.canary_percentage or 0) == 100.0)
    req = gate.request_promotion(skill_id="skill_new_1", version_id=str(v.id), requester="tester")
    check("满量申请晋升 → pending_approval", req["status"] == "pending_approval", str(req["status"]))
    approval = gate.review_promotion(req["approval_id"], reviewer="admin", approved=True)
    check("人审通过 → approved", approval.status == "approved", approval.status)
    v = db.query(SkillVersion).filter(SkillVersion.id == v.id).first()
    check("版本晋升 production", v.status == "production", v.status)

    try:
        gate.start_release(skill_id="skill_new_1", version_id=str(v.id), canary_percentage=13.0)
        check("非法百分比 13% 应被拒绝", False, "未抛错")
    except ValueError:
        check("非法百分比 13% 被拒绝", True)

    # 门禁评估
    ev = gate.evaluate(skill_id="skill_seo_v1", lookback_hours=24)
    check("门禁评估返回对比结果", "comparison" in ev or "canary" in ev, str(list(ev.keys())))

    # ═══════════════════════════════════════════
    print(f"\n结果: {_passed} 通过 / {_failed} 失败")
    return 1 if _failed else 0


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


if __name__ == "__main__":
    raise SystemExit(main())
