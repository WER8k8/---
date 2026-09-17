# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""每日自主运营闭环 — 串联所有步骤。

运行顺序：
1. 技术雷达扫描 → 更新策略 (⑤)
2. GEO 探测 → 品牌曝光检测
3. SEO 内容生成 → GEO 评分 → 不合格重写 (②)
4. 多平台发布 → 收录监控
5. 询盘处理 → 归因记录 (①)
6. 数据归因分析 (⑥)
7. 排名对比 → 反馈到策略 (④)

每个步骤独立 try/except，单步失败不阻塞后续步骤。
可通过环境变量 DAILY_AUTONOMOUS_CYCLE_ACTIVE=true/false 控制开关。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger("uj-admin.daily_autonomous_cycle")

# ---------------------------------------------------------------------------
# 步骤结果数据结构
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    step_name: str
    step_number: int
    description: str
    success: bool
    duration_ms: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""


def _now_iso() -> str:
    """_now_iso。
    :return: 返回处理结果。
    """
    return datetime.now(timezone.utc).isoformat()


def _safe_asyncio_run(coro):
    """兼容已有事件循环（FastAPI）和无事件循环（Celery）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════════════════
# Step 1: 技术雷达扫描 → 更新策略 (⑤)
# ═══════════════════════════════════════════════════════════════════════════

def _step_tech_radar() -> StepResult:
    """抓取 GEO/SEO 技术雷达，更新 tactics changelog。"""
    from app.services.geo.tech_radar_fetch import fetch_latest_geo_techniques, update_tactics_from_radar
    t0 = time.monotonic()
    try:
        findings = fetch_latest_geo_techniques()
        items = findings.get("items") or []
        update = update_tactics_from_radar(items, min_score=0.5)
        return StepResult(
            step_name="tech_radar",
            step_number=1,
            description="技术雷达扫描 → 更新策略",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "items_fetched": findings.get("total", 0),
                "sources_ok": findings.get("sources_ok", 0),
                "sources_total": findings.get("sources_total", 0),
                "changelog_entries_added": update.get("changelog_entries_added", 0),
                "new_tactics_version": update.get("new_tactics_version", ""),
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="tech_radar",
            step_number=1,
            description="技术雷达扫描 → 更新策略",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# Step 2: GEO 探测 → 品牌曝光检测
# ═══════════════════════════════════════════════════════════════════════════

def _step_geo_probe(db) -> StepResult:
    """运行 Hermes 每日排名循环，包含多引擎 GEO probe + 平台发现。"""
    from app.services.hermes.daily_rank_ops import run_hermes_daily_rank_cycle
    t0 = time.monotonic()
    try:
        report = run_hermes_daily_rank_cycle(db, trigger="daily_autonomous_cycle")
        summary = report.get("summary") or {}
        return StepResult(
            step_name="geo_probe",
            step_number=2,
            description="GEO 探测 → 品牌曝光检测",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "recommend_pass_rate": summary.get("recommend_pass_rate"),
                "regression_detected": summary.get("regression_detected"),
                "live_platform_coverage": summary.get("live_platform_coverage"),
                "rank_guard_passed": summary.get("rank_guard_passed"),
                "ecc_verdict": (report.get("ecc_review") or {}).get("verdict"),
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="geo_probe",
            step_number=2,
            description="GEO 探测 → 品牌曝光检测",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# Step 3: SEO 内容生成 → GEO 评分 → 不合格重写 (②)
# ═══════════════════════════════════════════════════════════════════════════

def _step_content_gen(db) -> StepResult:
    """触发 Hermes 持续迭代闭环：Research Brief → ECC → 部门路由。"""
    from app.services.hermes.hermes_continuous_iteration_service import run_continuous_iteration_cycle
    t0 = time.monotonic()
    try:
        report = run_continuous_iteration_cycle(
            db,
            trigger="daily_autonomous_cycle",
            force=False,
            include_deerflow_drain=True,
        )
        skipped = report.get("skipped", False)
        ecc = report.get("ecc") or {}
        return StepResult(
            step_name="content_gen",
            step_number=3,
            description="SEO 内容生成 → GEO 评分 → 不合格重写",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "skipped": skipped,
                "skip_reason": report.get("reason", ""),
                "brief_id": (report.get("brief") or {}).get("brief_id"),
                "ecc_verdict": ecc.get("verdict"),
                "department_count": len(report.get("department_routing") or []),
                "deerflow_processed": (report.get("deerflow_pending") or {}).get("processed", 0),
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="content_gen",
            step_number=3,
            description="SEO 内容生成 → GEO 评分 → 不合格重写",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# Step 4: 多平台发布 → 收录监控
# ═══════════════════════════════════════════════════════════════════════════

def _step_publish_monitor(db) -> StepResult:
    """运行 DeerFlow 定时更新（含 pending drain + 多租户发布）。"""
    from app.services.ubrain.deerflow_scheduled_service import run_scheduled_deerflow_update
    t0 = time.monotonic()
    try:
        report = run_scheduled_deerflow_update(db, trigger="daily_autonomous_cycle")
        return StepResult(
            step_name="publish_monitor",
            step_number=4,
            description="多平台发布 → 收录监控",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "processed_tenants": report.get("processed_tenants", 0),
                "skipped": report.get("skipped", False),
                "skip_reason": report.get("reason", ""),
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="publish_monitor",
            step_number=4,
            description="多平台发布 → 收录监控",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# Step 5: 询盘处理 → 归因记录 (①)
# ═══════════════════════════════════════════════════════════════════════════

def _step_inquiry_process(db) -> StepResult:
    """查询近期询盘统计，检查归因字段完整性。"""
    from sqlalchemy import func
    from app.models.inquiry import Inquiry
    t0 = time.monotonic()
    try:
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)
        new_24h = (
            db.query(func.count(Inquiry.id))
            .filter(Inquiry.is_active, Inquiry.created_at >= cutoff_24h)
            .scalar() or 0
        )
        new_7d = (
            db.query(func.count(Inquiry.id))
            .filter(Inquiry.is_active, Inquiry.created_at >= cutoff_7d)
            .scalar() or 0
        )
        total = db.query(func.count(Inquiry.id)).filter(Inquiry.is_active).scalar() or 0
        # 归因覆盖率
        with_attribution = (
            db.query(func.count(Inquiry.id))
            .filter(Inquiry.is_active, Inquiry.attribution_channel.isnot(None))
            .scalar() or 0
        )
        attr_rate = round(with_attribution / total, 4) if total else 0.0
        return StepResult(
            step_name="inquiry_process",
            step_number=5,
            description="询盘处理 → 归因记录",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "new_inquiries_24h": new_24h,
                "new_inquiries_7d": new_7d,
                "total_active": total,
                "attribution_coverage": attr_rate,
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="inquiry_process",
            step_number=5,
            description="询盘处理 → 归因记录",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# Step 6: 数据归因分析 (⑥)
# ═══════════════════════════════════════════════════════════════════════════

def _step_attribution(db) -> StepResult:
    """构建全漏斗归因报告。"""
    from app.services.attribution_service import build_attribution_report
    t0 = time.monotonic()
    try:
        report = build_attribution_report(db, period="7d")
        return StepResult(
            step_name="attribution",
            step_number=6,
            description="数据归因分析",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "total_inquiries": report.get("total_inquiries", 0),
                "total_quoted": report.get("total_quoted", 0),
                "total_closed": report.get("total_closed", 0),
                "overall_quote_rate": report.get("overall_quote_rate", 0),
                "overall_close_rate": report.get("overall_close_rate", 0),
                "total_revenue": report.get("total_revenue", 0),
                "top_keywords_count": len(report.get("top_keywords") or []),
                "top_engines_count": len(report.get("top_ai_engines") or []),
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="attribution",
            step_number=6,
            description="数据归因分析",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# Step 7: 排名对比 → 反馈到策略 (④)
# ═══════════════════════════════════════════════════════════════════════════

def _step_rank_feedback(db) -> StepResult:
    """对比排名快照，如有回归则写入反馈。"""
    from app.services.hermes.daily_rank_ops import load_rank_ops_snapshot
    t0 = time.monotonic()
    try:
        snapshot = load_rank_ops_snapshot() or {}
        summary = snapshot.get("summary") or {}
        today_rate = summary.get("recommend_pass_rate", 0)
        yesterday_rate = summary.get("yesterday_pass_rate")
        regression = summary.get("regression_detected", False)
        feedback: list[str] = []
        if regression:
            feedback.append("排名回归：对比昨日 probe 通过率下降，优先补强 FAQ/参数/platform 矩阵")
        if today_rate and today_rate < 0.25:
            feedback.append("recommend 通过率过低，建议触发 geo_content_matrix 人审发稿")
        if not feedback:
            feedback.append("排名稳定，继续保持当前策略")

        return StepResult(
            step_name="rank_feedback",
            step_number=7,
            description="排名对比 → 反馈到策略",
            success=True,
            duration_ms=(time.monotonic() - t0) * 1000,
            data={
                "today_pass_rate": today_rate,
                "yesterday_pass_rate": yesterday_rate,
                "regression_detected": regression,
                "feedback_actions": feedback,
                "has_snapshot": snapshot is not None,
            },
        )
    except Exception as exc:
        return StepResult(
            step_name="rank_feedback",
            step_number=7,
            description="排名对比 → 反馈到策略",
            success=False,
            duration_ms=(time.monotonic() - t0) * 1000,
            error=str(exc)[:300],
        )


# ═══════════════════════════════════════════════════════════════════════════
# 主循环
# ═══════════════════════════════════════════════════════════════════════════

def _run_cycle_steps(db) -> list[StepResult]:
    """依次执行 7 个闭环步骤并返回结果列表。"""
    plan: list[tuple[str, Any, bool]] = [
        ("技术雷达扫描 → 更新策略", _step_tech_radar, False),
        ("GEO 探测 → 品牌曝光检测", _step_geo_probe, True),
        ("SEO 内容生成 → GEO 评分 → 不合格重写", _step_content_gen, True),
        ("多平台发布 → 收录监控", _step_publish_monitor, True),
        ("询盘处理 → 归因记录", _step_inquiry_process, True),
        ("数据归因分析", _step_attribution, True),
        ("排名对比 → 反馈到策略", _step_rank_feedback, True),
    ]
    steps: list[StepResult] = []
    total = len(plan)
    for idx, (label, fn, needs_db) in enumerate(plan, start=1):
        logger.info("[Step %d/%d] %s", idx, total, label)
        result = fn(db) if needs_db else fn()
        steps.append(result)
        logger.info(
            "[Step %d/%d] done: success=%s duration=%sms",
            idx, total, result.success, f"{result.duration_ms:.0f}",
        )
    return steps


def _build_cycle_body(
    *,
    trigger: str,
    steps: list[StepResult],
    total_ms: float,
    succeeded: int,
    failed: int,
) -> dict[str, Any]:
    """汇总闭环执行结果为返回体。"""
    return {
        "trigger": trigger,
        "started_at": _now_iso(),
        "completed_at": _now_iso(),
        "total_duration_ms": round(total_ms, 1),
        "steps_succeeded": succeeded,
        "steps_failed": failed,
        "steps_total": len(steps),
        "steps": [
            {
                "step": s.step_number,
                "name": s.step_name,
                "description": s.description,
                "success": s.success,
                "duration_ms": round(s.duration_ms, 1),
                "data": s.data,
                "error": s.error or None,
            }
            for s in steps
        ],
    }


def _save_cycle_snapshot(body: dict[str, Any]) -> None:
    """将闭环快照写入 Redis（最新 + 按日），失败仅告警。"""
    try:
        from app.core.cache import redis_client
        import json
        if redis_client:
            redis_client.set(
                "hermes:daily_autonomous_cycle:latest",
                json.dumps(body, ensure_ascii=False),
                ex=86400 * 14,
            )
            day = datetime.now(timezone.utc).strftime("%Y%m%d")
            redis_client.set(
                f"hermes:daily_autonomous_cycle:day:{day}",
                json.dumps(body, ensure_ascii=False),
                ex=86400 * 90,
            )
    except Exception as exc:
        logger.warning("Failed to save daily cycle snapshot: %s", exc)


def run_daily_autonomous_cycle(
    db=None,
    *,
    trigger: str = "scheduler",
) -> dict[str, Any]:
    """每日自主运营闭环主入口。

    串联 7 个步骤，每步独立 try/except 保证单步失败不阻塞后续。
    返回完整的执行摘要。

    Args:
        db: SQLAlchemy Session（可选，部分步骤需要；不传则自动创建）
        trigger: 触发来源标识

    Returns:
        包含各步骤结果、总耗时、成功/失败计数的摘要字典
    """
    cycle_start = time.monotonic()
    owns_db = db is None
    if owns_db:
        db = SessionLocal()

    try:
        logger.info("Daily autonomous cycle started (trigger=%s)", trigger)
        steps = _run_cycle_steps(db)
        # --- 汇总 ---
        total_ms = (time.monotonic() - cycle_start) * 1000
        succeeded = sum(1 for s in steps if s.success)
        failed = sum(1 for s in steps if not s.success)
        body = _build_cycle_body(
            trigger=trigger,
            steps=steps,
            total_ms=total_ms,
            succeeded=succeeded,
            failed=failed,
        )
        _save_cycle_snapshot(body)
        logger.info(
            "Daily autonomous cycle finished: %d/%d succeeded, total=%sms",
            succeeded, len(steps), f"{total_ms:.0f}",
        )
        return body

    finally:
        if owns_db:
            db.close()


# ═══════════════════════════════════════════════════════════════════════════
# 调度器（每日定时执行）
# ═══════════════════════════════════════════════════════════════════════════

class DailyAutonomousCycleScheduler:
    """每日自主运营闭环调度器 — daemon 线程，每日定时执行一次。"""
    _instance = None
    _running = False
    def __new__(cls):
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.last_run = None
            cls._instance.run_count = 0
            cls._instance.errors: list[str] = []
            cls._instance.last_report: dict[str, Any] | None = None
        return cls._instance

    def start(self, *, bootstrap: bool = False) -> dict[str, str]:
        """start。

        参数说明：
        :param self: 参数 self
        :param bootstrap: 参数 bootstrap
        :return: 返回处理结果。
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        hour = int(getattr(settings, "DAILY_AUTONOMOUS_CYCLE_HOUR", 6) or 6)
        minute = int(getattr(settings, "DAILY_AUTONOMOUS_CYCLE_MINUTE", 0) or 0)
        threading.Thread(target=self._loop, args=(hour, minute), daemon=True).start()
        if bootstrap:
            threading.Thread(target=self._bootstrap, daemon=True).start()
        logger.info(
            "DailyAutonomousCycleScheduler started daily=%02d:%02d bootstrap=%s",
            hour, minute, bootstrap,
        )
        return {"status": "started"}

    def _bootstrap(self) -> None:
        """启动后延迟执行一次（让其他服务先就绪）。"""
        time.sleep(60)
        if not self._running:
            return
        try:
            self.run_once(trigger="bootstrap")
        except Exception as exc:
            logger.exception("Daily autonomous cycle bootstrap failed")
            self.errors.append(str(exc))

    def stop(self) -> dict[str, str]:
        """stop。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._running = False
        return {"status": "stopped"}

    def _loop(self, check_hour: int, check_minute: int) -> None:
        """_loop。

        参数说明：
        :param self: 参数 self
        :param check_hour: 参数 check_hour
        :param check_minute: 参数 check_minute
        :return: 返回处理结果。
        """
        while self._running:
            now = datetime.now()
            next_run = now.replace(
                hour=check_hour, minute=check_minute, second=0, microsecond=0,
            )
            if now >= next_run:
                from datetime import timedelta
                next_run += timedelta(days=1)
            wait = (next_run - now).total_seconds()
            slept = 0.0
            while self._running and slept < wait:
                chunk = min(120.0, wait - slept)
                time.sleep(chunk)
                slept += chunk
            if not self._running:
                break
            try:
                self.run_once(trigger="scheduler")
            except Exception as exc:
                logger.exception("Daily autonomous cycle scheduled run failed")
                self.errors.append(str(exc))

    def run_once(self, *, trigger: str = "scheduler") -> dict[str, Any]:
        """run_once。

        参数说明：
        :param self: 参数 self
        :param trigger: 参数 trigger
        :return: 返回处理结果。
        """
        from app.services.scheduler_leader import release_scheduler_lock, try_acquire_scheduler_lock
        if not try_acquire_scheduler_lock("daily_autonomous_cycle", ttl_seconds=7200):
            return {"skipped": True, "reason": "leader_lock_busy", "trigger": trigger}
        try:
            report = run_daily_autonomous_cycle(trigger=trigger)
            self.last_run = report.get("completed_at")
            self.run_count += 1
            self.last_report = report
            return report
        except Exception as exc:
            logger.exception("Daily autonomous cycle run failed")
            self.errors.append(str(exc))
            raise
        finally:
            release_scheduler_lock("daily_autonomous_cycle")

    def status(self) -> dict[str, Any]:
        """status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        from app.core.cache import redis_client
        import json
        latest = None
        if redis_client:
            try:
                raw = redis_client.get("hermes:daily_autonomous_cycle:latest")
                if raw:
                    latest = json.loads(raw)
            except Exception:
                pass

        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "schedule": {
                "hour": int(getattr(settings, "DAILY_AUTONOMOUS_CYCLE_HOUR", 6) or 6),
                "minute": int(getattr(settings, "DAILY_AUTONOMOUS_CYCLE_MINUTE", 0) or 0),
            },
            "latest_snapshot": latest,
            "errors": self.errors[-5:],
        }


# 模块级单例
daily_autonomous_cycle_scheduler = DailyAutonomousCycleScheduler()
