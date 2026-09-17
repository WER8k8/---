# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 7×24 巡站维护 — 只读探测 + 建议，不执行破坏性操作。"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ai_key_probe import ai_key_status
from app.services.hermes.maintenance_constitution import (
    CONSTITUTION_SUMMARY,
    CONSTITUTION_VERSION,
    assert_maintenance_action,
    constitution_payload,
)
from app.services.hermes.site_patrol_store import load_patrol_snapshot, save_patrol_snapshot
from app.services.nvidia_customer_probe_store import load_probe_snapshot
from app.services.production_readiness_service import run_readiness_checks
from app.services.publish_queue_service import queue_stats
from app.services.scenario_health_store import load_health_snapshot

logger = logging.getLogger("uj-admin.hermes_site_patrol")


def _probe_readiness(db: Session) -> dict[str, Any]:
    """_probe_readiness。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    report = run_readiness_checks(db)
    score = report.score
    return {
        "id": "readiness",
        "title": "生产就绪检查",
        "status": "pass" if report.ready else "fail",
        "ready": report.ready,
        "score": score,
        "failures": [
            c.to_dict()
            for c in report.checks
            if c.status == "fail" and c.required
        ][:8],
        "warnings": [
            c.to_dict()
            for c in report.checks
            if c.status == "warn"
        ][:5],
    }


def _probe_ai_connect(db: Session) -> dict[str, Any]:
    """_probe_ai_connect。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    st = ai_key_status(db)
    ok = bool(st.get("has_real_key"))
    return {
        "id": "ai_connect",
        "title": "AI 通道配置",
        "status": "pass" if ok else "warn",
        "has_real_key": ok,
        "providers": st.get("providers") or [],
        "environment": st.get("environment"),
        "mvp_launch": st.get("mvp_launch"),
    }


def _probe_scenario_health(db: Session) -> dict[str, Any]:
    """_probe_scenario_health。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    snap = load_health_snapshot(db)
    if not snap:
        return {
            "id": "scenario_health",
            "title": "AI 场景健康快照",
            "status": "warn",
            "message": "尚无巡检快照，建议手动运行场景健康检查",
            "healthy_count": 0,
            "total": 0,
        }
    unhealthy = int(snap.get("unhealthy_count") or 0)
    total = int(snap.get("total") or 0)
    healthy = int(snap.get("healthy_count") or 0)
    status = "pass" if unhealthy == 0 and total > 0 else ("warn" if unhealthy < total else "fail")
    return {
        "id": "scenario_health",
        "title": "AI 场景健康快照",
        "status": status,
        "healthy_count": healthy,
        "unhealthy_count": unhealthy,
        "total": total,
        "saved_at": snap.get("saved_at"),
        "unhealthy_scenarios": [
            {
                "scenario": s.get("scenario"),
                "label": s.get("label"),
                "error": (s.get("error") or "")[:120],
            }
            for s in (snap.get("scenarios") or [])
            if not s.get("healthy")
        ][:6],
    }


def _probe_nvidia_customer(db: Session) -> dict[str, Any]:
    """_probe_nvidia_customer。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    snap = load_probe_snapshot(db)
    if not snap:
        return {
            "id": "nvidia_customer_probe",
            "title": "英伟达客户模型探测",
            "status": "warn",
            "message": "尚无探测快照",
        }
    unhealthy = int(snap.get("unhealthy_count") or 0)
    total = int(snap.get("total") or 0)
    status = "pass" if unhealthy == 0 and total > 0 else ("warn" if unhealthy < total else "fail")
    return {
        "id": "nvidia_customer_probe",
        "title": "英伟达客户模型探测",
        "status": status,
        "healthy_count": snap.get("healthy_count"),
        "unhealthy_count": unhealthy,
        "total": total,
        "saved_at": snap.get("saved_at"),
    }


def _probe_http_gateway() -> dict[str, Any]:
    """_probe_http_gateway。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    base = (
        getattr(settings, "HERMES_SITE_PATROL_HTTP_SELF_URL", None)
        or "http://127.0.0.1:8001"
    ).rstrip("/")
    url = f"{base}/api/v1/ops/readiness/public"
    started = time.perf_counter()
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(url)
        latency_ms = int((time.perf_counter() - started) * 1000)
        ok = resp.status_code < 400
        body: dict[str, Any] = {}
        try:
            body = resp.json()
        except Exception:
            pass
        data = body.get("data") if isinstance(body, dict) else {}
        return {
            "id": "http_gateway",
            "title": "API 网关可达",
            "status": "pass" if ok else "fail",
            "url": url,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
            "ready": (data or {}).get("ready") if isinstance(data, dict) else None,
        }
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "id": "http_gateway",
            "title": "API 网关可达",
            "status": "fail",
            "url": url,
            "latency_ms": latency_ms,
            "error": str(exc)[:200],
        }


def _probe_publish_queue(db: Session) -> dict[str, Any]:
    """_probe_publish_queue。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    stats = queue_stats(db)
    pending = int(stats.get("pending") or 0)
    failed = int(stats.get("failed") or 0)
    status = "fail" if failed > 50 else ("warn" if pending > 200 or failed > 10 else "pass")
    return {
        "id": "publish_queue",
        "title": "发布队列（只读）",
        "status": status,
        "stats": stats,
    }


def _probe_seo_rank_scheduler(db: Session) -> dict[str, Any]:
    """_probe_seo_rank_scheduler。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    enabled = bool(getattr(settings, "RANK_SCHEDULER_ENABLED", False))
    rank_status: dict[str, Any] | None = None
    if enabled:
        try:
            from app.services.rank_scheduler import rank_scheduler
            rank_status = rank_scheduler.get_status()
        except Exception as exc:
            rank_status = {"error": str(exc)[:200]}
    running = bool((rank_status or {}).get("running"))
    if not enabled:
        status = "warn"
    elif running:
        status = "pass"
    else:
        status = "fail"
    return {
        "id": "seo_rank_scheduler",
        "title": "SEO 关键词排名调度",
        "status": status,
        "enabled": enabled,
        "running": running,
        "rank_scheduler": rank_status,
    }


def _probe_video_workers(db: Session) -> dict[str, Any]:
    """_probe_video_workers。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    from app.services.publish_workers.tier_router import preflight_workers
    preflight = preflight_workers()
    ready = bool(preflight.get("ready"))
    return {
        "id": "video_workers",
        "title": "视频矩阵 Worker 预检",
        "status": "pass" if ready else "warn",
        "ready": ready,
        "preflight": preflight,
    }


def _probe_seo_inclusion(db: Session) -> dict[str, Any]:
    """_probe_seo_inclusion。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    from app.models.content import InclusionStatus
    total = db.query(InclusionStatus).count()
    included = (
        db.query(InclusionStatus).filter(InclusionStatus.is_included.is_(True)).count()
    )
    if total == 0:
        return {
            "id": "seo_inclusion",
            "title": "SEO 收录监控",
            "status": "warn",
            "total": 0,
            "included": 0,
            "inclusion_rate": 0,
            "message": "尚无收录记录",
        }
    rate = included / total
    not_included = total - included
    status = "fail" if rate < 0.5 else ("warn" if not_included / total >= 0.3 else "pass")
    return {
        "id": "seo_inclusion",
        "title": "SEO 收录监控",
        "status": status,
        "total": total,
        "included": included,
        "not_included": not_included,
        "inclusion_rate": round(rate * 100, 2),
    }


def _probe_agency_llm(db: Session) -> dict[str, Any]:
    """_probe_agency_llm。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not getattr(settings, "HERMES_AGENCY_LLM_ENABLED", True):
        return {
            "id": "agency_llm",
            "title": "Agency LLM 路由",
            "status": "warn",
            "message": "HERMES_AGENCY_LLM_ENABLED=false",
            "available_count": 0,
            "total": 0,
        }
    from app.services.hermes.agency.llm_router import list_providers
    rows = list_providers(probe=True)
    avail = sum(1 for p in rows if p.get("available"))
    total = len(rows)
    if avail == 0:
        status = "fail"
    elif avail < 2:
        status = "warn"
    else:
        status = "pass"
    ready = [p["id"] for p in rows if p.get("available")]
    missing = [p["id"] for p in rows if not p.get("available")][:5]
    return {
        "id": "agency_llm",
        "title": "Agency LLM 路由（ao 10 provider）",
        "status": status,
        "available_count": avail,
        "total": total,
        "ready_providers": ready,
        "missing_sample": missing,
        "chain": getattr(settings, "HERMES_AGENCY_PROVIDER_CHAIN", ""),
    }


def _probe_deerflow_queue(db: Session) -> dict[str, Any]:
    """_probe_deerflow_queue。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    from app.models.deerflow_job import DeerflowJob
    counts: dict[str, int] = {}
    for st in ("queued", "running", "failed"):
        counts[st] = db.query(DeerflowJob).filter(DeerflowJob.status == st).count()
    failed = counts.get("failed", 0)
    queued = counts.get("queued", 0)
    status = "fail" if failed > 20 else ("warn" if queued > 50 or failed > 5 else "pass")
    return {
        "id": "deerflow_queue",
        "title": "DeerFlow 任务队列（只读）",
        "status": status,
        "counts": counts,
    }


PROBE_REGISTRY: list[Callable[..., dict[str, Any]]] = [
    _probe_readiness,
    _probe_ai_connect,
    _probe_scenario_health,
    _probe_nvidia_customer,
    _probe_http_gateway,
    _probe_publish_queue,
    _probe_seo_rank_scheduler,
    _probe_seo_inclusion,
    _probe_video_workers,
    _probe_agency_llm,
    _probe_deerflow_queue,
]


def _suggest_platform_health(by_id: dict[str, Any]) -> list[dict[str, str]]:
    """就绪检查 / AI Key / 场景健康 / 网关相关的整改建议。"""
    out: list[dict[str, str]] = []
    if by_id.get("readiness", {}).get("status") == "fail":
        out.append(
            {
                "severity": "high",
                "suggestion": "生产就绪检查未通过：请人工核对 JWT/数据库/环境变量（巡站不会自动修改配置）。",
            }
        )
    if not by_id.get("ai_connect", {}).get("has_real_key"):
        out.append(
            {
                "severity": "medium",
                "suggestion": "未检测到有效 AI Key：请在超管「模型配置」或环境变量中配置（巡站不会写入 Key）。",
            }
        )
    sh = by_id.get("scenario_health", {})
    if int(sh.get("unhealthy_count") or 0) > 0:
        out.append(
            {
                "severity": "medium",
                "suggestion": "部分 AI 场景不健康：建议超管运行「场景健康巡检」（巡站仅读取快照，不自动切换模型）。",
            }
        )
    if by_id.get("http_gateway", {}).get("status") == "fail":
        out.append(
            {
                "severity": "critical",
                "suggestion": "API 网关不可达：请检查进程/反向代理/端口（巡站不会重启服务）。",
            }
        )
    return out


def _suggest_publish_seo(by_id: dict[str, Any]) -> list[dict[str, str]]:
    """发布队列与 SEO 排名/收录相关的整改建议。"""
    out: list[dict[str, str]] = []
    pq = by_id.get("publish_queue", {})
    if int((pq.get("stats") or {}).get("failed") or 0) > 10:
        out.append(
            {
                "severity": "medium",
                "suggestion": "发布队列失败堆积：请运维人工排查 Worker（巡站不会自动重试发布）。",
            }
        )
    seo = by_id.get("seo_rank_scheduler", {})
    if not seo.get("enabled"):
        out.append(
            {
                "severity": "low",
                "suggestion": "SEO 排名调度未开启：生产环境可设 RANK_SCHEDULER_ENABLED=true 并重启后端。",
            }
        )
    elif seo.get("status") == "fail":
        out.append(
            {
                "severity": "medium",
                "suggestion": "SEO 排名调度已配置但未运行：请检查 RankScheduler 线程是否启动。",
            }
        )
    inc = by_id.get("seo_inclusion", {})
    if inc.get("status") == "fail":
        out.append(
            {
                "severity": "high",
                "suggestion": f"收录率过低（{inc.get('inclusion_rate', 0)}%）：建议运行收录复检并排查发布 URL。",
            }
        )
    elif inc.get("status") == "warn" and int(inc.get("not_included") or 0) > 0:
        out.append(
            {
                "severity": "medium",
                "suggestion": f"有 {inc.get('not_included')} 条未收录：可在司令部触发收录复检。",
            }
        )
    return out


def _suggest_workers_llm(by_id: dict[str, Any]) -> list[dict[str, str]]:
    """视频 Worker / DeerFlow 队列 / Agency LLM 相关的整改建议。"""
    out: list[dict[str, str]] = []
    vw = by_id.get("video_workers", {})
    if not vw.get("ready"):
        out.append(
            {
                "severity": "medium",
                "suggestion": "视频矩阵 Worker 未就绪：请配置 SAU / biliup / 小红书 MCP / AiToEarn 至少一种。",
            }
        )
    dfq = by_id.get("deerflow_queue", {})
    if int((dfq.get("counts") or {}).get("failed") or 0) > 5:
        out.append(
            {
                "severity": "medium",
                "suggestion": "DeerFlow 失败任务堆积：请在超管司令部查看队列并人工 rerun（巡站不会自动重跑）。",
            }
        )
    al = by_id.get("agency_llm", {})
    if al.get("status") == "fail":
        out.append(
            {
                "severity": "high",
                "suggestion": (
                    "Agency LLM 无可用 provider：请在 .env 配置 AI_DEEPSEEK_API_KEY 并启动 Ollama"
                    "（deploy/production/agency-llm-compose.yml）；CLI OAuth 仅适合本机。"
                ),
            }
        )
    elif al.get("status") == "warn":
        out.append(
            {
                "severity": "medium",
                "suggestion": f"Agency LLM 仅 {al.get('available_count', 0)}/{al.get('total', 0)} 可用，"
                "建议补充 deepseek/ollama API 或运行 scripts/setup-agency-llm-providers.sh",
            }
        )
    return out


def _build_suggestions(probes: list[dict[str, Any]]) -> list[dict[str, str]]:
    """_build_suggestions。

    参数说明：
    :param probes: 参数 probes
    :return: 返回处理结果。
    """
    assert_maintenance_action("suggest_remediation")
    by_id = {p["id"]: p for p in probes}
    out: list[dict[str, str]] = []
    out.extend(_suggest_platform_health(by_id))
    out.extend(_suggest_publish_seo(by_id))
    out.extend(_suggest_workers_llm(by_id))
    if not out:
        out.append(
            {
                "severity": "info",
                "suggestion": "各探测项正常；下一轮巡站将继续只读监测。",
            }
        )
    return out


def _overall_status(probes: list[dict[str, Any]]) -> str:
    """_overall_status。

    参数说明：
    :param probes: 参数 probes
    :return: 返回处理结果。
    """
    statuses = [p.get("status") for p in probes]
    if "fail" in statuses:
        return "critical"
    if "warn" in statuses:
        return "degraded"
    return "healthy"


def run_site_patrol(db: Session, *, trigger: str = "manual") -> dict[str, Any]:
    """执行一轮巡站（只读 + 写巡站快照）。"""
    assert_maintenance_action("read_probe")
    started = time.perf_counter()
    probes: list[dict[str, Any]] = []
    errors: list[str] = []
    for fn in PROBE_REGISTRY:
        try:
            if fn is _probe_http_gateway:
                probes.append(fn())
            else:
                probes.append(fn(db))
        except Exception as exc:
            logger.exception("Patrol probe failed: %s", getattr(fn, "__name__", fn))
            errors.append(str(exc))
            probes.append(
                {
                    "id": getattr(fn, "__name__", "unknown"),
                    "title": "探测异常",
                    "status": "fail",
                    "error": str(exc)[:200],
                }
            )

    suggestions = _build_suggestions(probes)
    assert_maintenance_action("emit_alert")
    if _overall_status(probes) != "healthy":
        logger.warning(
            "Hermes site patrol %s: status=%s fails=%s",
            trigger,
            _overall_status(probes),
            [p["id"] for p in probes if p.get("status") == "fail"],
        )

    body: dict[str, Any] = {
        "constitution_version": CONSTITUTION_VERSION,
        "constitution_summary": CONSTITUTION_SUMMARY,
        "trigger": trigger,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "overall_status": _overall_status(probes),
        "probes": probes,
        "suggestions": suggestions,
        "errors": errors,
        "probe_count": len(probes),
        "pass_count": sum(1 for p in probes if p.get("status") == "pass"),
        "warn_count": sum(1 for p in probes if p.get("status") == "warn"),
        "fail_count": sum(1 for p in probes if p.get("status") == "fail"),
    }
    return save_patrol_snapshot(db, body)


def patrol_status(db: Session) -> dict[str, Any]:
    """patrol_status。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    snap = load_patrol_snapshot(db)
    from app.services.hermes.site_patrol_scheduler import hermes_site_patrol_scheduler
    return {
        "constitution": constitution_payload(),
        "scheduler": hermes_site_patrol_scheduler.status(),
        "latest": snap,
    }
