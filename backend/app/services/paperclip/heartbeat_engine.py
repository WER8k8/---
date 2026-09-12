"""Paperclip 心跳调度引擎。

以 daemon 线程定时扫描所有 heartbeat_enabled=True 且到期的 Agent，
执行心跳：检查预算 → 查询 pending tasks → 分派执行 → 记录结果。
使用 Redis leader lock 防止多实例重复执行。
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.paperclip import (
    PaperclipAgent,
    PaperclipCompany,
    PaperclipHeartbeat,
    PaperclipTask,
)
from app.services.paperclip.budget_guard import check_budget, consume_credits

logger = logging.getLogger("uj-admin.paperclip_heartbeat")


def _bridge(db: Session):
    """影子双写桥（轮24-B）：TASK_CONTROL_ENABLED 关时完全旁路，桥内自吞异常。"""
    from app.services.tasks.paperclip_bridge import PaperclipTaskBridge
    return PaperclipTaskBridge(db)

# 心跳锁名称
_LEADER_LOCK = "paperclip_heartbeat"
# 最小扫描间隔（秒）
_MIN_TICK_INTERVAL = 30


def _acquire_leader() -> bool:
    """获取 leader lock，防止多实例重复执行。"""
    try:
        from app.services.scheduler_leader import try_acquire_scheduler_lock
        return try_acquire_scheduler_lock(_LEADER_LOCK, ttl_seconds=300)
    except Exception:
        logger.debug("scheduler_leader unavailable, fallback to single-instance mode")
        return True


def _release_leader() -> None:
    """释放 leader lock。"""
    try:
        from app.services.scheduler_leader import release_scheduler_lock
        release_scheduler_lock(_LEADER_LOCK)
    except Exception:
        pass


class PaperclipHeartbeatEngine:
    """心跳调度引擎（单例模式）。

    通过 daemon 线程定时执行心跳循环。
    """
    _instance: PaperclipHeartbeatEngine | None = None
    _running: bool = False
    def __new__(cls) -> PaperclipHeartbeatEngine:
        """__new__。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.last_run: str | None = None
            cls._instance.run_count: int = 0
            cls._instance.errors: list[str] = []
        return cls._instance

    def start(self) -> dict[str, str]:
        """启动心跳调度器。

        Returns:
            启动状态
        """
        if self._running:
            return {"status": "already_running"}
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info("PaperclipHeartbeatEngine started")
        return {"status": "started"}

    def stop(self) -> dict[str, str]:
        """停止心跳调度器。

        Returns:
            停止状态
        """
        self._running = False
        logger.info("PaperclipHeartbeatEngine stopped")
        return {"status": "stopped"}

    def _loop(self) -> None:
        """主循环：定时执行 tick。"""
        while self._running:
            try:
                self.tick()
            except Exception as exc:
                logger.exception("Paperclip heartbeat tick failed")
                self.errors.append(str(exc)[:200])
                # 保留最近 50 条错误
                if len(self.errors) > 50:
                    self.errors = self.errors[-50:]

            # 等待下一轮（可中断）
            waited = 0.0
            while self._running and waited < _MIN_TICK_INTERVAL:
                time.sleep(1.0)
                waited += 1.0

    def tick(self) -> dict[str, Any]:
        """单次心跳循环：查询所有 heartbeat_enabled=True 且到期的 Agent，执行心跳。

        Returns:
            本轮心跳统计
        """
        if not _acquire_leader():
            return {"skipped": True, "reason": "leader_lock_busy"}
        try:
            return self._tick_inner()
        finally:
            _release_leader()

    def _tick_inner(self) -> dict[str, Any]:
        """内部 tick 实际逻辑。"""
        db = SessionLocal()
        stats = {"checked": 0, "executed": 0, "skipped": 0, "errors": 0}
        try:
            now = datetime.now(timezone.utc)
            agents = db.query(PaperclipAgent).filter(
                PaperclipAgent.heartbeat_enabled == True,  # noqa: E712
                PaperclipAgent.status == "active",
            ).all()
            for agent in agents:
                stats["checked"] += 1
                try:
                    interval = int(agent.heartbeat_interval_minutes or 240)
                    last = agent.last_heartbeat_at
                    if last:
                        elapsed = (now - last).total_seconds() / 60.0
                        if elapsed < interval:
                            stats["skipped"] += 1
                            continue

                    self._execute_heartbeat(db, agent)
                    stats["executed"] += 1
                except Exception as exc:
                    stats["errors"] += 1
                    logger.warning(
                        "Heartbeat failed for agent %s: %s", agent.id, exc,
                    )

            self.last_run = now.isoformat()
            self.run_count += 1
            logger.info("Heartbeat tick: %s", stats)
            return stats
        finally:
            db.close()

    def _execute_heartbeat(self, db: Session, agent: PaperclipAgent) -> None:
        """执行单个 Agent 的心跳。

        流程：
        1. 检查预算
        2. 查询 pending tasks
        3. 对每个 task 根据 intent 分派执行
        4. 记录心跳结果
        """
        now = datetime.now(timezone.utc)
        agent_id = str(agent.id)
        company_id = str(agent.company_id)
        # 创建心跳记录
        heartbeat = PaperclipHeartbeat(
            agent_id=agent_id,
            company_id=company_id,
            status="running",
            trigger="schedule",
            started_at=now,
        )
        db.add(heartbeat)
        db.commit()
        db.refresh(heartbeat)
        total_credits = 0.0
        tasks_checked = 0
        tasks_executed = 0
        results: list[dict[str, Any]] = []
        error_msg: str | None = None
        try:
            # 1. 检查预算
            budget = check_budget(db, agent_id)
            if not budget.get("allowed"):
                heartbeat.status = "skipped"
                heartbeat.error_message = f"budget_exhausted: {budget.get('reason', '')}"
                heartbeat.finished_at = datetime.now(timezone.utc)
                db.commit()
                return

            # 2. 查询 pending tasks
            pending_tasks = db.query(PaperclipTask).filter(
                PaperclipTask.assigned_agent_id == agent_id,
                PaperclipTask.status.in_(["queued", "blocked"]),
            ).order_by(PaperclipTask.priority.asc(), PaperclipTask.created_at.asc()).limit(5).all()
            # 2.5 加载租户业务上下文（产品/询盘/行业），注入任务执行
            tenant_ctx_prompt = ""
            try:
                company = db.query(PaperclipCompany).filter(PaperclipCompany.id == company_id).first()
                if company and company.tenant_id:
                    from app.services.paperclip.tenant_context import build_agent_mission_prompt
                    tenant_ctx_prompt = build_agent_mission_prompt(db, str(company.tenant_id))
            except Exception as ctx_exc:
                logger.debug("tenant context load failed: %s", ctx_exc)

            tasks_checked = len(pending_tasks)
            # 3. 逐个执行
            for task in pending_tasks:
                try:
                    task_result = self._dispatch_task(db, agent, task)
                    tasks_executed += 1
                    credits_used = float(task_result.get("credits_used", 0.0))
                    total_credits += credits_used
                    results.append({
                        "task_id": str(task.id),
                        "status": task_result.get("status", "unknown"),
                        "credits": credits_used,
                    })
                except Exception as exc:
                    logger.warning("Task %s dispatch failed: %s", task.id, exc)
                    results.append({
                        "task_id": str(task.id),
                        "status": "error",
                        "error": str(exc)[:200],
                    })

            # 4. 扣费
            if total_credits > 0:
                consume_credits(db, agent_id, total_credits)

            # 5. 更新心跳记录
            heartbeat.status = "success"
            heartbeat.tasks_checked = tasks_checked
            heartbeat.tasks_executed = tasks_executed
            heartbeat.credits_used = total_credits
            heartbeat.result_json = json.dumps(results, ensure_ascii=False)
            heartbeat.finished_at = datetime.now(timezone.utc)
            # 更新 Agent 最后心跳时间
            agent.last_heartbeat_at = now
            db.commit()

        except Exception as exc:
            heartbeat.status = "failed"
            heartbeat.error_message = str(exc)[:500]
            heartbeat.finished_at = datetime.now(timezone.utc)
            db.commit()
            raise

    def _dispatch_task(
        self,
        db: Session,
        agent: PaperclipAgent,
        task: PaperclipTask,
    ) -> dict[str, Any]:
        """根据 task.intent 将任务分派给 DeerFlow 或 Hermes 执行。

        Args:
            db: 数据库 session
            agent: Agent 记录
            task: 任务记录

        Returns:
            执行结果
        """
        intent = (task.intent or "").strip()
        agent_ref = (agent.agent_ref or "").strip()
        provider = (agent.provider or "hermes").strip()
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        db.commit()
        _bridge(db).on_task_running(task)
        result: dict[str, Any] = {}
        try:
            if provider == "deerflow" or intent in (
                "lead_content_pack", "find_buyers", "outreach_letter_pack",
                "market_research", "geo_submit_pack", "geo_content_matrix",
                "matrix_publish", "flywheel_loop",
            ):
                result = self._run_via_deerflow(db, agent, task, intent)
            elif provider == "hermes" and agent_ref:
                result = self._run_via_hermes(db, agent, task, agent_ref)
            else:
                # 默认通过 DeerFlow 通用 intent 执行
                result = self._run_via_deerflow(db, agent, task, intent or "generic")

            task.status = "success"
            task.result_json = json.dumps(result, ensure_ascii=False)
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
            _bridge(db).on_task_finished(task, success=True)
            # 尝试冒泡更新目标进度
            if task.goal_id:
                try:
                    from app.services.paperclip.goal_chain import update_progress
                    update_progress(db, str(task.goal_id))
                except Exception:
                    pass

        except Exception as exc:
            task.status = "failed"
            task.result_json = json.dumps({"error": str(exc)[:500]}, ensure_ascii=False)
            task.finished_at = datetime.now(timezone.utc)
            db.commit()
            _bridge(db).on_task_finished(task, success=False)
            raise

        return result

    def _run_via_deerflow(
        self,
        db: Session,
        agent: PaperclipAgent,
        task: PaperclipTask,
        intent: str,
    ) -> dict[str, Any]:
        """通过 DeerFlow 任务队列执行。"""
        from app.services.ubrain.deerflow_job_service import enqueue_job, run_job
        company = db.query(PaperclipCompany).filter(
            PaperclipCompany.id == agent.company_id,
        ).first()
        tenant_id = str(company.tenant_id) if company else str(agent.company_id)
        # 注入租户业务上下文到 DeerFlow payload
        business_ctx: dict[str, Any] = {}
        try:
            from app.services.paperclip.tenant_context import build_tenant_business_context
            business_ctx = build_tenant_business_context(db, tenant_id)
        except Exception:
            pass

        job = enqueue_job(
            db,
            tenant_id=tenant_id,
            intent=intent,
            payload={
                "message": task.title,
                "context": {
                    "task_id": str(task.id),
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "agent_role": agent.role,
                    "description": task.description,
                    "paperclip": True,
                    "business_context": business_ctx,
                },
            },
            created_by=f"paperclip_agent:{agent.id}",
        )
        task.deerflow_job_id = job.id
        db.commit()
        job_result = run_job(db, str(job.id))
        credits_used = 10.0  # 基础积分消耗
        return {
            "status": job_result.get("status", "unknown"),
            "job_id": str(job.id),
            "result": job_result.get("result"),
            "credits_used": credits_used,
        }

    def _run_via_hermes(
        self,
        db: Session,
        agent: PaperclipAgent,
        task: PaperclipTask,
        plugin_id: str,
    ) -> dict[str, Any]:
        """通过 Hermes 插件运行时执行。"""
        from app.services.hermes.runtime import execute_plugin
        company = db.query(PaperclipCompany).filter(
            PaperclipCompany.id == agent.company_id,
        ).first()
        tenant_id = str(company.tenant_id) if company else str(agent.company_id)
        result = execute_plugin(
            db,
            tenant_id=tenant_id,
            plugin_id=plugin_id,
            message=task.title,
            context={
                "task_id": str(task.id),
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "agent_role": agent.role,
                "description": task.description,
                "paperclip": True,
            },
        )
        credits_used = 5.0  # Hermes 基础积分消耗
        return {
            "status": "success",
            "plugin_result": result,
            "credits_used": credits_used,
        }

    def trigger_heartbeat(self, db: Session, agent_id: str) -> dict[str, Any]:
        """手动触发指定 Agent 的心跳。

        Args:
            db: 数据库 session
            agent_id: Agent ID

        Returns:
            执行结果
        """
        agent = db.query(PaperclipAgent).filter(PaperclipAgent.id == agent_id).first()
        if not agent:
            return {"error": "agent_not_found"}

        try:
            self._execute_heartbeat(db, agent)
            return {"status": "executed", "agent_id": agent_id}
        except Exception as exc:
            logger.warning("Manual heartbeat failed for agent %s: %s", agent_id, exc)
            return {"status": "failed", "error": str(exc)[:200]}

    def status(self) -> dict[str, Any]:
        """返回引擎状态。"""
        return {
            "running": self._running,
            "last_run": self.last_run,
            "run_count": self.run_count,
            "recent_errors": self.errors[-5:],
        }


# 模块级单例
paperclip_heartbeat_engine = PaperclipHeartbeatEngine()


# ---------------------------------------------------------------------------
# Module-level API wrappers
# ---------------------------------------------------------------------------

def list_company_heartbeats(db: Session, company_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """列出公司心跳记录。"""
    rows = (
        db.query(PaperclipHeartbeat)
        .filter(PaperclipHeartbeat.company_id == company_id)
        .order_by(PaperclipHeartbeat.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(h.id),
            "agent_id": str(h.agent_id),
            "company_id": str(h.company_id),
            "status": h.status,
            "trigger": h.trigger,
            "tasks_checked": h.tasks_checked,
            "tasks_executed": h.tasks_executed,
            "credits_used": h.credits_used,
            "result_json": h.result_json,
            "error_message": h.error_message,
            "started_at": h.started_at.isoformat() if h.started_at else None,
            "finished_at": h.finished_at.isoformat() if h.finished_at else None,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in rows
    ]


def trigger_manual_heartbeat(db: Session, agent_id: str) -> dict[str, Any] | None:
    """手动触发指定 Agent 的心跳。"""
    return paperclip_heartbeat_engine.trigger_heartbeat(db, agent_id)


def engine_status() -> dict[str, Any]:
    """心跳引擎状态。"""
    return paperclip_heartbeat_engine.status()


def start_engine(db: Session) -> dict[str, Any]:
    """启动心跳引擎。"""
    return paperclip_heartbeat_engine.start()


def stop_engine() -> dict[str, Any]:
    """停止心跳引擎。"""
    return paperclip_heartbeat_engine.stop()
