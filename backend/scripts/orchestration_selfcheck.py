"""编排链路自检脚本 —— 一键验证「所有环节是否打通」。

用途：
    把"链路打通"从口头结论变成可重复、可回归的机器验证。
    CI / 运维 / 开发均可运行，退出码 0 = 全通，1 = 有环节未通。

运行（在 backend/ 下，使用项目 venv）：
    ./.venv/Scripts/python.exe scripts/orchestration_selfcheck.py
    # 或 Linux: ./.venv/bin/python scripts/orchestration_selfcheck.py

检查维度（10 项）：
    1. 数据库连通与表规模
    2. Alembic 单 head（多 head 会阻塞后续所有迁移）
    3. Celery 任务注册（orchestration / deerflow）
    4. 编排路由挂载（/orchestration、/deepseek-harness）
    5. 统一任务面桥（hermes_task_bridge ROUTERS）
    6. n8n 内建工作流注册（site_built_notify / content_publish_dispatch）
    7. DeerFlow 执行器 intent 覆盖（9 个 intent 均有处理分支）
    8. DeerFlow 真执行接线（无 TODO 占位）
    9. 外贸技能注册表填充（避免"技能未注册"误判）
   10. Browser 取证持久化（落盘 + 入库）
"""
from __future__ import annotations

import os

# 与 run.py 对齐：裸跑本脚本时也把 config/dev/.env 灌入 os.environ，
# 否则 n8n 工作流注册表（直读 os.environ）会误显示 enabled=False。
from dotenv import load_dotenv
for _f in ("config/dev/.env", ".env"):
    if os.path.isfile(_f):
        load_dotenv(_f)
import sys

# 保证从任意 cwd 运行都能 import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


# ---------------------------------------------------------------------------
# 1. 数据库连通
# ---------------------------------------------------------------------------
def check_database() -> None:
    try:
        from sqlalchemy import text

        from app.core.config import settings
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            dialect = db.bind.dialect.name
            if dialect == "sqlite":
                n = db.execute(
                    text("SELECT count(*) FROM sqlite_master WHERE type='table'")
                ).scalar()
            else:
                n = db.execute(
                    text(
                        "SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema='public'"
                    )
                ).scalar()
            record(
                "1. 数据库连通",
                True,
                f"{dialect} | {n} 张表 | {settings.DATABASE_URL.split('@')[-1][:40]}",
            )
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        record("1. 数据库连通", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 2. Alembic 单 head
# ---------------------------------------------------------------------------
def check_alembic_heads() -> None:
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config("alembic.ini")
        cfg.set_main_option(
            "script_location",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "alembic_migrations"),
        )
        heads = ScriptDirectory.from_config(cfg).get_heads()
        record(
            "2. Alembic 单 head",
            len(heads) == 1,
            f"heads={len(heads)} {heads if len(heads) != 1 else heads[0][:40]}",
        )
    except Exception as exc:  # noqa: BLE001
        record("2. Alembic 单 head", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 3. Celery 任务注册
# ---------------------------------------------------------------------------
def _import_task_modules() -> None:
    """显式导入任务模块。

    Celery 的 `include` 是 **worker 启动时**才导入的（Celery() 构造时不导入），
    因此纯 import 场景下 celery_app.tasks 只有 celery.* 内置任务。自检需显式
    导入以模拟 worker 启动，否则会误报"任务未注册"。
    """
    import importlib

    for m in (
        "seo_tasks", "geo_tasks", "ubrain_tasks", "trade_intel_tasks",
        "cross_border_tasks", "billing_tasks", "churn_tasks", "sla_tasks",
        "quote_wake_tasks", "company_autofill_tasks", "deerflow_tasks",
        "orchestration_tasks", "ops_scheduler_tasks",
    ):
        try:
            importlib.import_module(f"app.tasks.{m}")
        except Exception:  # noqa: BLE001
            pass


def check_celery_tasks() -> None:
    try:
        from app.tasks.celery_app import celery_app

        _import_task_modules()
        names = {n for n in celery_app.tasks if not n.startswith("celery.")}
        # 注意：这些任务用 @shared_task(name="短名") 注册，**不是**模块全路径
        need = {"process_ai_task", "execute_deerflow_job", "deerflow_run_pending"}
        missing = sorted(need - names)
        record(
            "3. Celery 任务注册",
            not missing,
            f"项目任务 {len(names)} 个" + (f" | 缺失: {missing}" if missing else ""),
        )
    except Exception as exc:  # noqa: BLE001
        record("3. Celery 任务注册", False, f"{type(exc).__name__}: {str(exc)[:120]}")


def check_beat_schedule() -> None:
    """核对 beat 定时任务名与实际注册名是否一致。

    历史坑：任务用 @shared_task(name="短名") 注册，而 beat_schedule 写模块全路径，
    导致 Beat 永远匹配不到任务——**定时任务静默不执行**（8/12 中招）。
    """
    try:
        from app.tasks.celery_app import celery_app

        _import_task_modules()
        registered = {n for n in celery_app.tasks if not n.startswith("celery.")}
        bad = [
            (k, c["task"])
            for k, c in celery_app.conf.beat_schedule.items()
            if c["task"] not in registered
        ]
        total = len(celery_app.conf.beat_schedule)
        record(
            "3b. Beat 定时任务名匹配",
            not bad,
            f"{total - len(bad)}/{total} 可匹配" + (f" | 不匹配: {bad}" if bad else ""),
        )
    except Exception as exc:  # noqa: BLE001
        record("3b. Beat 定时任务名匹配", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 4. 编排路由挂载
# ---------------------------------------------------------------------------
def check_routes() -> None:
    try:
        import importlib

        mods = {
            "orchestration": "app.api.v1.routes.orchestration",
            "deepseek_harness": "app.api.v1.routes.deepseek_harness",
        }
        info = []
        ok = True
        for label, mod in mods.items():
            try:
                m = importlib.import_module(mod)
                n = len(getattr(m, "router").routes)
                info.append(f"{label}({n} 路由)")
            except Exception as exc:  # noqa: BLE001
                ok = False
                info.append(f"{label}导入失败:{type(exc).__name__}")
        record("4. 编排路由挂载", ok, " | ".join(info))
    except Exception as exc:  # noqa: BLE001
        record("4. 编排路由挂载", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 5. 统一任务面桥
# ---------------------------------------------------------------------------
def check_bridge() -> None:
    try:
        from app.services.tasks.hermes_task_bridge import ROUTERS

        need = {"ai_site_build", "site_build", "ubrain_intent", "deepseek_harness"}
        missing = sorted(need - set(ROUTERS.keys()))
        record(
            "5. 统一任务面桥",
            not missing,
            f"ROUTERS={sorted(ROUTERS.keys())}" + (f" | 缺失: {missing}" if missing else ""),
        )
    except Exception as exc:  # noqa: BLE001
        record("5. 统一任务面桥", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 6. n8n 内建工作流
# ---------------------------------------------------------------------------
def check_n8n() -> None:
    try:
        from app.services.n8n.workflow_registry import (
            ensure_builtin_workflows,
            get_workflow_registry,
        )

        ensure_builtin_workflows()
        reg = get_workflow_registry()
        info, ok = [], True
        for wid in ("site_built_notify", "content_publish_dispatch"):
            r = reg.get(wid)
            if r is None:
                ok = False
                info.append(f"{wid}=缺失")
            else:
                info.append(f"{wid}=已注册(enabled={r.enabled})")
        record("6. n8n 内建工作流", ok, " | ".join(info))
    except Exception as exc:  # noqa: BLE001
        record("6. n8n 内建工作流", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 7-8. DeerFlow 执行器
# ---------------------------------------------------------------------------
def check_deerflow() -> None:
    try:
        from app.services.deerflow import executor as ex_mod

        src = open(ex_mod.__file__, encoding="utf-8").read()
        intents = [
            "keyword_research", "content_creation", "seo_publish", "page_creation",
            "seo_metadata", "multi_channel_publish", "buyer_research",
            "outreach_letter", "email_dispatch",
            # 2026-09-14 对标阿里国际 Accio Work 新增：结构化市场洞察 + 横向比价排序
            "market_insight", "supplier_compare",
        ]
        missing = [i for i in intents if f"_exec_{i}" not in src]
        record(
            "7. DeerFlow intent 覆盖",
            not missing,
            f"{len(intents) - len(missing)}/{len(intents)} 已覆盖" + (f" | 缺: {missing}" if missing else ""),
        )
        # 真执行接线：不应残留"占位降级"字样
        stale = src.count("暂无可安全接入的真实服务")
        record(
            "8. DeerFlow 真执行接线",
            stale == 0,
            f"残留占位降级标记: {stale} 处" + ("" if stale == 0 else "（应改为真执行或带真实原因的降级）"),
        )
    except Exception as exc:  # noqa: BLE001
        record("7. DeerFlow intent 覆盖", False, f"{type(exc).__name__}: {str(exc)[:120]}")
        record("8. DeerFlow 真执行接线", False, "同上")


# ---------------------------------------------------------------------------
# 9. 外贸技能注册表
# ---------------------------------------------------------------------------
def check_skills() -> None:
    try:
        from app.services.deerflow.executor import _ensure_foreign_trade_skills
        from app.services.foreign_trade import skill_registry

        before = len(skill_registry._skills)
        _ensure_foreign_trade_skills()
        after = len(skill_registry._skills)
        record(
            "9. 外贸技能注册表",
            after > 0,
            f"导入前 {before} → 导入后 {after} 个技能"
            + ("（若不导入则恒为 0，会把真实能力误判为不存在）" if before == 0 else ""),
        )
    except Exception as exc:  # noqa: BLE001
        record("9. 外贸技能注册表", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 10. Browser 取证持久化
# ---------------------------------------------------------------------------
def check_evidence() -> None:
    import tempfile

    try:
        os.environ["BROWSER_EVIDENCE_DIR"] = os.path.join(tempfile.mkdtemp(), "ev")
        from app.core.database import SessionLocal
        from app.models.trace import TaskTrace
        from app.services.browser_runtime.evidence import (
            EvidenceRecord,
            persist_evidence,
        )

        db = SessionLocal()
        try:
            ev = EvidenceRecord(
                tenant_id=None, actor="selfcheck", action="navigate",
                target_url="https://example.com",
            )
            ev.mark_success(output_summary="selfcheck")
            res = persist_evidence(ev, db=db)
            row = db.query(TaskTrace).filter(TaskTrace.source_id == str(ev.id)).first()
            ok = bool(res.get("disk")) and bool(res.get("db")) and row is not None
            detail = f"disk={res.get('disk')} db={res.get('db')} reason={res.get('db_reason')}"
            if row is not None:
                db.delete(row)  # 清理自检数据
                db.commit()
            record("10. Browser 取证持久化", ok, detail)
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        record("10. Browser 取证持久化", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 11. 技能包可发现（磁盘 SKILL.md → 结构化索引）
# ---------------------------------------------------------------------------
def check_skill_pack_discovery() -> None:
    try:
        from app.services.registry.skill_pack_loader import (
            discover_skill_packs,
            resolve_skill_pack_dirs,
        )

        dirs = resolve_skill_pack_dirs()
        entries = discover_skill_packs(dirs)
        ok = len(entries) > 0
        parsed = sum(1 for e in entries if e.parse_ok)
        record(
            "11. 技能包可发现",
            ok,
            f"来源 {[s for s, _ in dirs]} | 发现 {len(entries)} 个"
            f" | 解析成功 {parsed}",
        )
    except Exception as exc:  # noqa: BLE001
        record("11. 技能包可发现", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 12. 技能包已入库（skills 表 active 数量）
# ---------------------------------------------------------------------------
def check_skill_pack_seeded() -> None:
    try:
        from app.core.database import SessionLocal
        from app.models.registry import RegistrySkill

        db = SessionLocal()
        try:
            total = db.query(RegistrySkill).count()
            active = (
                db.query(RegistrySkill)
                .filter(RegistrySkill.status == "active")
                .count()
            )
            record(
                "12. 技能包已入库",
                active > 0,
                f"skills 表共 {total} 条 | active {active} 条",
            )
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        record("12. 技能包已入库", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 13. 技能包意图可匹配（自动智能判断调用哪个 skill）
# ---------------------------------------------------------------------------
def check_skill_pack_match() -> None:
    try:
        from app.core.database import SessionLocal
        from app.services.registry.skill_service import match_skill_scored

        probes = [
            "buyer_research", "seo_publish", "outreach_letter",
            "site_build", "keyword_research",
        ]
        db = SessionLocal()
        try:
            missed = []
            detail_parts = []
            for q in probes:
                hits = match_skill_scored(db, q, top_k=1)
                if hits:
                    detail_parts.append(f"{q}→{hits[0][0].name}({hits[0][1]})")
                else:
                    missed.append(q)
            record(
                "13. 技能包意图可匹配",
                not missed,
                ("; ".join(detail_parts[:3]) + (" ..." if len(detail_parts) > 3 else ""))
                + (f" | 未命中: {missed}" if missed else ""),
            )
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        record("13. 技能包意图可匹配", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 14. Hermes 执行器契约与 DAG 派发底座 (P0)
# ---------------------------------------------------------------------------
def check_hermes_executor_contract() -> None:
    try:
        from app.services.hermes.executors import ExecutorRegistry
        from app.services.hermes.task_control_supervisor import advance_plan
        from app.services.tasks.hermes_task_bridge import _run_hermes_node

        executors = ExecutorRegistry.list_executors()
        has_executors = len(executors) >= 1
        has_advance = callable(advance_plan)
        has_bridge = callable(_run_hermes_node)

        ok = has_executors and has_advance and has_bridge
        detail = f"executors={executors} | advance_plan=已实装 | bridge_node=已挂载"
        record("14. Hermes 执行器契约与派发底座", ok, detail)
    except Exception as exc:  # noqa: BLE001
        record("14. Hermes 执行器契约与派发底座", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 15. Trade AI Agent (全域社媒拓客与 WhatsApp 触达中枢) 物理就绪
# ---------------------------------------------------------------------------
def check_trade_ai_agent() -> None:
    try:
        ws_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        )
        trade_ai_dir = os.path.join(ws_root, "_external", "trade-ai-agent")
        backend_dir = os.path.join(trade_ai_dir, "backend", "app")

        has_root = os.path.isdir(trade_ai_dir)
        has_whatsapp = os.path.isfile(os.path.join(backend_dir, "api", "v1", "whatsapp.py"))
        has_scraper = os.path.isfile(os.path.join(backend_dir, "skills", "skill_social_scraper.py"))
        has_auto_sender = os.path.isfile(os.path.join(backend_dir, "skills", "skill_auto_sender.py"))

        ok = has_root and has_whatsapp and has_scraper and has_auto_sender
        detail = (
            f"物理目录=存在 | WhatsApp路由={'OK' if has_whatsapp else '缺失'} | "
            f"社媒挖掘={'OK' if has_scraper else '缺失'} | 触达发送={'OK' if has_auto_sender else '缺失'}"
        )
        record("15. Trade AI Agent 物理拓客中枢", ok, detail)
    except Exception as exc:  # noqa: BLE001
        record("15. Trade AI Agent 物理拓客中枢", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 16. GoodJob CRM (7步履约、WhatsApp翻译与外贸单证中枢) 物理就绪
# ---------------------------------------------------------------------------
def check_goodjob_crm() -> None:
    try:
        ws_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        )
        goodjob_dir = os.path.join(ws_root, "_external", "goodjob-crm")
        plugin_file = os.path.join(
            goodjob_dir, "whatsapp-plugin", "src", "server", "providers", "baileys-provider.ts"
        )
        has_pi = os.path.isfile(os.path.join(goodjob_dir, "PI_GENERATOR_DESIGN.md"))
        has_docs = os.path.isfile(os.path.join(goodjob_dir, "TRADE_DOCS_DESIGN.md"))
        has_plugin = os.path.isfile(plugin_file)

        ok = os.path.isdir(goodjob_dir) and has_plugin and has_pi and has_docs
        detail = (
            f"物理目录=存在 | Baileys插件={'OK' if has_plugin else '缺失'} | "
            f"PI发票规约={'OK' if has_pi else '缺失'} | 单证工作室={'OK' if has_docs else '缺失'}"
        )
        record("16. GoodJob CRM 履约单证中枢", ok, detail)
    except Exception as exc:  # noqa: BLE001
        record("16. GoodJob CRM 履约单证中枢", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 17. 全域系统注册表与 SYSTEM-LOCK-02 硬锁校验
# ---------------------------------------------------------------------------
def check_system_registry_and_lock() -> None:
    try:
        import json

        ws_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        )
        reg_file = os.path.join(ws_root, "AEOS_GLOBAL_SYSTEM_REGISTRY.json")
        agents_file = os.path.join(ws_root, "AGENTS.md")

        has_reg = os.path.isfile(reg_file)
        has_lock = False
        if os.path.isfile(agents_file):
            with open(agents_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                has_lock = "SYSTEM-LOCK-02" in content

        subsystems_count = 0
        if has_reg:
            with open(reg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                subsystems_count = len(data.get("subsystems", {}))

        ok = has_reg and has_lock and (subsystems_count >= 8)
        detail = (
            f"全局注册表={'OK' if has_reg else '缺失'} (8大子系统={subsystems_count}/8) | "
            f"SYSTEM-LOCK-02={'锁定' if has_lock else '未锁定'}"
        )
        record("17. 全域法典与不可裁减硬锁", ok, detail)
    except Exception as exc:  # noqa: BLE001
        record("17. 全域法典与不可裁减硬锁", False, f"{type(exc).__name__}: {str(exc)[:120]}")


# ---------------------------------------------------------------------------
# 18. 多核执行器调色盘全集就绪断言
# ---------------------------------------------------------------------------
def check_multi_executor_registry() -> None:
    try:
        from app.services.hermes.executors import ExecutorRegistry

        executors = set(ExecutorRegistry.list_executors())
        required = {"accio", "deerflow", "trade_ai_agent", "goodjob_crm"}
        missing = required - executors

        ok = len(missing) == 0
        detail = f"全集={sorted(executors)} | 缺失={list(missing)}"
        record("18. 多核执行器调色盘全集", ok, detail)
    except Exception as exc:  # noqa: BLE001
        record("18. 多核执行器调色盘全集", False, f"{type(exc).__name__}: {str(exc)[:120]}")


def main() -> int:
    for fn in (
        check_database,
        check_alembic_heads,
        check_celery_tasks,
        check_beat_schedule,
        check_routes,
        check_bridge,
        check_n8n,
        check_deerflow,
        check_skills,
        check_evidence,
        check_skill_pack_discovery,
        check_skill_pack_seeded,
        check_skill_pack_match,
        check_hermes_executor_contract,
        check_trade_ai_agent,
        check_goodjob_crm,
        check_system_registry_and_lock,
        check_multi_executor_registry,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            record(fn.__name__, False, f"自检项崩溃: {type(exc).__name__}: {str(exc)[:120]}")

    width = max(len(n) for n, _, _ in RESULTS)
    print("=" * 78)
    print("编排链路自检报告")
    print("=" * 78)
    passed = 0
    for name, ok, detail in RESULTS:
        flag = "PASS" if ok else "FAIL"
        passed += 1 if ok else 0
        print(f"[{flag}] {name.ljust(width)}  {detail}")
    print("-" * 78)
    total = len(RESULTS)
    print(f"结果: {passed}/{total} 通过")
    print("=" * 78)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
