"""智能体协同中心 — DeerFlow 任务真实数据（非硬编码队列）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.deerflow_job import DeerflowJob
from app.services.hermes.deerflow_ops_service import deerflow_slo_snapshot
from app.services.ubrain.deerflow_job_service import run_job, serialize_job_with_steps

INTENT_LABELS: dict[str, str] = {
    "market_research": "市场研究",
    "find_buyers": "找采购商",
    "outreach_letter_pack": "开发信编排",
    "lead_content_pack": "内容生成",
    "geo_submit_pack": "GEO 检查",
    "matrix_publish": "多平台发布",
    "inquiry_score": "询盘评分",
    "inquiry_reply_draft": "询盘回复草稿",
    "weekly_lead_report": "线索周报",
    "flywheel_loop": "卖货飞轮闭环",
    "osint_check": "客户背调",
    "website_icp": "官网 ICP 分析",
    "proforma_invoice": "形式发票 PI",
    "prospect_clean": "潜客清洗",
}

INTENT_AGENTS: dict[str, list[str]] = {
    "market_research": ["市场研究"],
    "find_buyers": ["找客Agent"],
    "outreach_letter_pack": ["开发信Agent"],
    "lead_content_pack": ["文案生成器"],
    "geo_submit_pack": ["SEO分析师"],
    "matrix_publish": ["发布Worker"],
    "flywheel_loop": ["市场研究", "找客Agent", "开发信Agent"],
    "osint_check": ["背调专员"],
    "website_icp": ["建站助手"],
    "proforma_invoice": ["谈单顾问"],
    "prospect_clean": ["找客Agent"],
}

# UBrain 编排器工具说明（MCP 桥接内置目录）
UBRAIN_TOOL_LABELS: dict[str, str] = {
    "find_buyers": "多渠道找采购商与线索",
    "outreach_letter_pack": "开发信与冷邮件编排",
    "negotiation_draft": "询盘谈单与还价草稿",
    "lead_content_pack": "获客内容包与 FAQ",
    "geo_content_matrix": "GEO 内容矩阵生成",
    "geo_submit_pack": "GEO 提交清单与 Schema 检查",
    "matrix_publish": "多平台矩阵发布",
    "inquiry_score": "询盘意向评分",
    "inquiry_draft": "询盘回复草稿",
    "weekly_lead_report": "线索周报",
    "publish_status": "发布任务状态",
    "ssl_status": "SSL 证书状态",
    "export_feasibility": "出口可行性分析",
    "blue_ocean": "蓝海市场扫描",
    "hs_lookup": "HS 编码查询",
    "market_research": "市场研究报告",
    "sync_feedback": "效果回流同步",
    "ops_snapshot": "运营快照",
    "general": "通用智能回复",
    "flywheel_loop": "卖货飞轮闭环",
    "osint_check": "六层 OSINT 客户背调",
    "website_icp": "官网 ICP 画像与 onboarding",
    "proforma_invoice": "形式发票 PI / 报价单",
    "prospect_clean": "潜客去重与意向打标",
}

# 用户通过 UI 登记的外部 MCP 服务（进程内缓存，重启清空）
_custom_mcp_servers: list[dict[str, Any]] = []


def _job_label(job: DeerflowJob) -> str:
    """_job_label。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    return INTENT_LABELS.get(job.intent or "", job.intent or "任务")


def _job_agents(job: DeerflowJob) -> list[str]:
    """_job_agents。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    return INTENT_AGENTS.get(job.intent or "", [job.intent or "Agent"])


def _format_dt(dt: datetime | None) -> str:
    """_format_dt。

    参数说明：
    :param dt: 参数 dt
    :return: 返回处理结果。
    """
    if not dt:
        return "-"
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _duration_seconds(job: DeerflowJob) -> float | None:
    """_duration_seconds。

    参数说明：
    :param job: 参数 job
    :return: 返回处理结果。
    """
    if job.started_at and job.finished_at:
        return (job.finished_at - job.started_at).total_seconds()
    return None


def _query_jobs(db: Session, *, tenant_id: str | None = None) -> Any:
    """_query_jobs。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    q = db.query(DeerflowJob)
    if tenant_id:
        q = q.filter(DeerflowJob.tenant_id == tenant_id)
    return q


def build_task_orchestrator(db: Session, *, tenant_id: str | None = None) -> dict[str, Any]:
    """build_task_orchestrator。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :return: 返回处理结果。
    """
    base = _query_jobs(db, tenant_id=tenant_id)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    active = base.filter(DeerflowJob.status == "running").count()
    queued = base.filter(DeerflowJob.status == "queued").count()
    completed_today = base.filter(
        DeerflowJob.status == "success",
        DeerflowJob.finished_at >= today_start,
    ).count()
    rows = base.order_by(DeerflowJob.created_at.desc()).limit(30).all()
    task_queue = [
        {
            "id": job.id,
            "name": _job_label(job),
            "agents": _job_agents(job),
            "priority": "高" if job.intent in ("flywheel_loop", "find_buyers") else "普通",
            "status": {
                "success": "done",
                "queued": "idle",
                "running": "running",
                "failed": "failed",
            }.get(job.status or "", "idle"),
            "lastRun": _format_dt(job.finished_at or job.created_at),
        }
        for job in rows
    ]
    return {
        "active_tasks": active,
        "queued_tasks": queued,
        "completed_today": completed_today,
        "task_queue": task_queue,
        "data_source": "deerflow_jobs",
    }


def build_execution_review(
    db: Session,
    *,
    tenant_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """build_execution_review。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param page: 参数 page
    :param page_size: 参数 page_size
    :return: 返回处理结果。
    """
    q = _query_jobs(db, tenant_id=tenant_id)
    total = q.count()
    rows = (
        q.order_by(DeerflowJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items: list[dict[str, Any]] = []
    durations: list[float] = []
    for job in rows:
        ser = serialize_job_with_steps(job)
        dur = _duration_seconds(job)
        if dur is not None:
            durations.append(dur)
        payload_msg = str((ser.get("payload") or {}).get("message") or "")
        result_raw = ser.get("result")
        output_len = len(str(result_raw)) if result_raw else 0
        items.append(
            {
                "id": job.id,
                "name": _job_label(job),
                "agents": " → ".join(_job_agents(job)),
                "duration": f"{dur:.1f}s" if dur is not None else "-",
                "tokens": str((result_raw or {}).get("tokens_used") or "-")
                if isinstance(result_raw, dict)
                else "-",
                "status": job.status,
                "time": _format_dt(job.finished_at or job.created_at),
                "input_len": len(payload_msg) if payload_msg else "-",
                "output_len": output_len or "-",
                "steps": ser.get("steps") or [],
            }
        )
    slo = deerflow_slo_snapshot(db)
    success_count = sum(1 for i in items if i.get("status") == "success")
    avg_dur = round(sum(durations) / len(durations), 1) if durations else slo.get("avg_run_seconds") or 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": {
            "total": total,
            "success_rate": round(success_count / len(items) * 100, 1) if items else 0,
            "avg_duration_sec": avg_dur,
            "failed_count": slo.get("failed_count", 0),
        },
        "data_source": "deerflow_jobs",
    }


def build_job_logs(db: Session, job_id: str) -> dict[str, Any]:
    """build_job_logs。

    参数说明：
    :param db: 参数 db
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        return {"lines": [], "name": "", "found": False}
    lines: list[dict[str, str]] = []
    for raw in (job.log_text or "").splitlines():
        text = raw.strip()
        if not text:
            continue
        ts = ""
        msg = text
        if text.startswith("[") and "]" in text:
            ts, msg = text[1:].split("]", 1)
            msg = msg.strip()
        lines.append({"ts": ts, "msg": msg})
    if not lines:
        for step in serialize_job_with_steps(job).get("steps") or []:
            lines.append({"ts": "", "msg": step.get("title") or ""})
    return {"lines": lines, "name": _job_label(job), "found": True}


def _ubrain_tool_ids() -> list[str]:
    """_ubrain_tool_ids。
    :return: 返回处理结果。
    """
    from app.services.ubrain.orchestrator import UBrainOrchestrator
    ids = list(UBrainOrchestrator.TOOLS)
    if "flywheel_loop" not in ids:
        ids.append("flywheel_loop")
    return ids


def build_mcp_tool_catalog() -> dict[str, Any]:
    """内置 UBrain/DeerFlow 工具目录（供 MCP 桥接 UI 展示）。"""
    items = [
        {
            "name": tool_id,
            "description": UBRAIN_TOOL_LABELS.get(tool_id, tool_id),
            "param_count": 1 if tool_id != "general" else 0,
        }
        for tool_id in _ubrain_tool_ids()
    ]
    return {"items": items, "total": len(items)}


def register_custom_mcp_server(*, name: str, url: str, protocol: str) -> dict[str, Any]:
    """register_custom_mcp_server。

    参数说明：
    :param name: 参数 name
    :param url: 参数 url
    :param protocol: 参数 protocol
    :return: 返回处理结果。
    """
    entry = {
        "name": name.strip(),
        "url": url.strip(),
        "protocol": (protocol or "http").lower(),
        "healthy": False,
        "tool_count": 0,
        "latency": 0,
    }
    _custom_mcp_servers[:] = [
        s for s in _custom_mcp_servers if s.get("name") != entry["name"]
    ]
    _custom_mcp_servers.append(entry)
    return entry


def build_mcp_bridge_status(db: Session) -> dict[str, Any]:
    """MCP 桥接概览：内置 DeerFlow 桥 + 用户登记的外部服务。"""
    catalog = build_mcp_tool_catalog()
    active = (
        db.query(DeerflowJob)
        .filter(DeerflowJob.status == "running")
        .count()
    )
    builtin_server = {
        "name": "UBrain DeerFlow Bridge",
        "url": "internal://deerflow-jobs",
        "protocol": "http",
        "healthy": True,
        "tool_count": catalog["total"],
        "latency": 0,
    }
    servers = [builtin_server, *_custom_mcp_servers]
    return {
        "status": "connected",
        "registered_tools": catalog["total"],
        "active_sessions": active,
        "tools": servers,
        "recent_calls": [],
        "data_source": "ubrain_orchestrator",
    }


def probe_mcp_server_health(*, name: str) -> dict[str, Any]:
    """probe_mcp_server_health。

    参数说明：
    :param name: 参数 name
    :return: 返回处理结果。
    """
    if name in ("", "default", "UBrain DeerFlow Bridge"):
        return {"healthy": True, "latency_ms": 0, "name": name or "UBrain DeerFlow Bridge"}
    for server in _custom_mcp_servers:
        if server.get("name") == name:
            return {
                "healthy": False,
                "latency_ms": 0,
                "name": name,
                "message": "外部 MCP 服务尚未接入探测，请确认服务已启动",
            }
    return {"healthy": False, "latency_ms": 0, "name": name, "message": "未找到 MCP 服务"}


def run_orchestrator_job(db: Session, job_id: str) -> dict[str, Any]:
    """run_orchestrator_job。

    参数说明：
    :param db: 参数 db
    :param job_id: 参数 job_id
    :return: 返回处理结果。
    """
    job = db.query(DeerflowJob).filter(DeerflowJob.id == job_id).first()
    if not job:
        return {"error": "任务不存在"}
    if job.status == "running":
        return {"error": "任务执行中", "status": job.status}
    try:
        return run_job(db, job_id)
    except ValueError:
        return {"error": "任务不存在"}


class AgentHubService:
    """兼容旧导出 — 委托 DeerFlow 队列函数。"""
    def build_task_orchestrator(self, db: Session, *, tenant_id: str | None = None) -> dict[str, Any]:
        """build_task_orchestrator。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :return: 返回处理结果。
        """
        return build_task_orchestrator(db, tenant_id=tenant_id)

    def build_execution_review(
        self,
        db: Session,
        *,
        tenant_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """build_execution_review。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param tenant_id: 参数 tenant_id
        :param page: 参数 page
        :param page_size: 参数 page_size
        :return: 返回处理结果。
        """
        return build_execution_review(
            db,
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
        )

    def build_job_logs(self, db: Session, job_id: str) -> dict[str, Any]:
        """build_job_logs。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :param job_id: 参数 job_id
        :return: 返回处理结果。
        """
        return build_job_logs(db, job_id)


agent_hub_service = AgentHubService()
