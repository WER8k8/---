# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""外贸研究员 — 只读信号 → ResearchBrief JSON（违宪动作禁止自动执行）。"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.cache import redis_client
from app.services.hermes.maintenance_constitution import CONSTITUTION_VERSION, assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_research_brief")

BRIEF_SNAPSHOT_KEY = "hermes:research_brief:latest"
BRIEF_DEDUPE_PREFIX = "hermes:research_brief:dedupe:"
BRIEF_INBOX_KEY = "hermes:research_brief:inbox"
INBOX_MAX = 100

# 24 槽位按 UTC 小时轮换（平台级，与租户 DeerFlow 日更互补）
HOURLY_TOPICS: tuple[dict[str, str], ...] = (
    {"key": "geo_rank", "lane": "GW-G", "label": "GEO 排名与 AEO 可见性", "category": "geo_rank"},
    {"key": "outreach_quality", "lane": "GW-L", "label": "开发信送达与反垃圾箱", "category": "paper"},
    {"key": "matrix_publish", "lane": "GW-S", "label": "矩阵发帖与平台绑定健康", "category": "structured_data"},
    {"key": "paid_attribution", "lane": "GW-P", "label": "UTM 归因与付费漏斗", "category": "performance"},
    {"key": "buyer_scout", "lane": "GW-L", "label": "找客画像与人工核实", "category": "paper"},
    {"key": "market_research", "lane": "GW-R", "label": "出口市场与品类机会", "category": "paper"},
    {"key": "inquiry_crm", "lane": "GW-L", "label": "询盘评分与 MEDDPICC", "category": "structured_data"},
    {"key": "content_variants", "lane": "GW-G", "label": "1→N 内容变体链路", "category": "frontend"},
    {"key": "social_etiquette", "lane": "GW-S", "label": "出海社媒礼仪与禁忌", "category": "paper"},
    {"key": "competitor_cf_b2b", "lane": "GW-PM", "label": "轻量 B2B 站竞品对照", "category": "paper"},
    {"key": "deerflow_tenant", "lane": "GW-R", "label": "DeerFlow 租户研究队列", "category": "backend"},
    {"key": "platform_health", "lane": "GW-PM", "label": "巡站与 API 可用性", "category": "backend"},
    {"key": "security_radar", "lane": "GW-PM", "label": "技术雷达与安全 CVE", "category": "backend"},
    {"key": "linkedin_b2b", "lane": "GW-S", "label": "LinkedIn B2B 内容节奏", "category": "paper"},
    {"key": "tiktok_export", "lane": "GW-S", "label": "TikTok 建材出海短视频", "category": "paper"},
    {"key": "email_warmup", "lane": "GW-L", "label": "域名预热与 SPF/DKIM", "category": "paper"},
    {"key": "aeo_citation", "lane": "GW-G", "label": "AI 引文与站点事实一致", "category": "geo_rank"},
    {"key": "rfq_negotiation", "lane": "GW-L", "label": "RFQ 谈单与成本底线", "category": "paper"},
    {"key": "site_onboarding", "lane": "GW-G", "label": "独立域建站向导缺口", "category": "frontend"},
    {"key": "ads_creative", "lane": "GW-P", "label": "广告创意人审导出", "category": "performance"},
    {"key": "pipeline_forecast", "lane": "GW-L", "label": "Pipeline 与赢单策略", "category": "structured_data"},
    {"key": "gw_backlog", "lane": "GW-PM", "label": "GW 登记册 P0 积压", "category": "paper"},
    {"key": "trade_disclaimer", "lane": "GW-R", "label": "贸易情报免责声明合规", "category": "paper"},
    {"key": "ops_rank", "lane": "GW-G", "label": "Hermes 排名攻坚日更", "category": "geo_rank"},
    {"key": "github_ecosystem_scout", "lane": "GW-PM", "label": "GitHub 生态侦察（专家代搜）", "category": "paper"},
)


def _repo_root() -> Path:
    """_repo_root。
    :return: 返回处理结果。
    """
    return Path(__file__).resolve().parents[4]


def _load_gw_register() -> dict[str, Any]:
    """_load_gw_register。
    :return: 返回处理结果。
    """
    path = _repo_root() / "docs" / "global-overseas-growth-task-register.json"
    if not path.is_file():
        return {"tasks": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("GW register read failed: %s", exc)
        return {"tasks": []}


def hourly_topic(*, at: datetime | None = None) -> dict[str, str]:
    """hourly_topic。

    参数说明：
    :param at: 参数 at
    :return: 返回处理结果。
    """
    now = at or datetime.now(timezone.utc)
    idx = now.hour % len(HOURLY_TOPICS)
    return dict(HOURLY_TOPICS[idx])


def collect_signals(db: Session | None = None) -> dict[str, Any]:
    """只读采集：运维快照、GW 登记册、DeerFlow 快照、巡站摘要。"""
    assert_maintenance_action("read_probe")
    signals: dict[str, Any] = {"collected_at": datetime.now(timezone.utc).isoformat()}
    try:
        from app.services.hermes.ops_autopilot import load_ops_snapshot
        signals["ops_snapshot"] = load_ops_snapshot() or {}
    except Exception as exc:
        signals["ops_snapshot"] = {"error": str(exc)[:200]}

    reg = _load_gw_register()
    pending_p0 = [
        t
        for t in reg.get("tasks") or []
        if t.get("priority") == "P0" and t.get("status") in ("pending", "in_progress")
    ]
    signals["gw_pending_p0"] = pending_p0[:12]
    signals["gw_pending_p0_count"] = len(pending_p0)
    try:
        from app.services.ubrain.deerflow_scheduled_service import load_deerflow_schedule_snapshot
        signals["deerflow"] = load_deerflow_schedule_snapshot() or {}
    except Exception as exc:
        signals["deerflow"] = {"error": str(exc)[:200]}

    patrol = (signals.get("ops_snapshot") or {}).get("patrol") or {}
    signals["patrol_summary"] = {
        "overall_status": patrol.get("overall_status"),
        "fail_count": patrol.get("fail_count"),
        "pass_count": patrol.get("pass_count"),
    }
    tech = (signals.get("ops_snapshot") or {}).get("tech_radar") or {}
    signals["tech_radar_summary"] = {
        "high_impact_count": tech.get("high_impact_count"),
        "expert_fail_count": tech.get("expert_fail_count"),
    }
    try:
        from app.services.hermes.github_ecosystem_scout_service import scout_summary_for_signals
        signals["github_scout"] = scout_summary_for_signals()
    except Exception as exc:
        signals["github_scout"] = {"error": str(exc)[:200]}

    return signals


def _brief_fingerprint(topic_key: str, finding: str) -> str:
    """_brief_fingerprint。

    参数说明：
    :param topic_key: 参数 topic_key
    :param finding: 参数 finding
    :return: 返回处理结果。
    """
    digest = hashlib.sha256(f"{topic_key}:{finding[:400]}".encode()).hexdigest()[:16]
    return digest


def _compose_finding(topic: dict[str, str], signals: dict[str, Any]) -> tuple[str, list[dict[str, Any]], str]:
    """规则合成 finding + evidence + impact。"""
    key = topic["key"]
    evidence: list[dict[str, Any]] = []
    impact = "low"
    if key == "gw_backlog":
        count = int(signals.get("gw_pending_p0_count") or 0)
        pending = signals.get("gw_pending_p0") or []
        titles = "；".join(t.get("title", "")[:40] for t in pending[:3])
        finding = f"GW 登记册仍有 {count} 条 P0 待办。优先关注：{titles or '无'}。"
        evidence.append({"type": "gw_register", "ref": "pending_p0_count", "value": count})
        impact = "high" if count >= 3 else "medium" if count else "low"

    elif key == "platform_health":
        ps = signals.get("patrol_summary") or {}
        fail = int(ps.get("fail_count") or 0)
        status = ps.get("overall_status") or "unknown"
        finding = f"巡站 overall={status}，失败探针 {fail} 个。建议人工查看 Hermes 运维快照，不自动修代码。"
        evidence.append({"type": "patrol", "ref": "fail_count", "value": fail})
        impact = "high" if fail >= 2 else "medium" if fail else "low"

    elif key == "security_radar":
        tr = signals.get("tech_radar_summary") or {}
        hi = int(tr.get("high_impact_count") or 0)
        ef = int(tr.get("expert_fail_count") or 0)
        finding = f"技术雷达 high_impact={hi}，专家 fail={ef}。高影响项须 ECC+人工，禁止热更新生产。"
        evidence.append({"type": "tech_radar", "ref": "high_impact_count", "value": hi})
        impact = "high" if hi or ef else "low"

    elif key == "deerflow_tenant":
        df = signals.get("deerflow") or {}
        enq = len(df.get("enqueued") or [])
        err = len(df.get("errors") or [])
        finding = (
            f"DeerFlow 最近槽位 enqueued={enq} errors={err}。"
            "租户 market_research 由日更调度；平台小时循环只读汇总，不重复入队。"
        )
        evidence.append({"type": "deerflow", "ref": "enqueued", "value": enq})
        impact = "medium" if err else "low"

    elif key == "outreach_quality":
        finding = (
            "开发信链路已接入 deliverability_summary（质量分、时区窗、跟进节奏、SPF 清单）。"
            "下一迭代：GW-P-TR-01 UTM 全链路与真实 webhook 打开率。"
        )
        evidence.append({"type": "code", "ref": "outreach_deliverability_service", "value": "shipped"})
        impact = "medium"

    elif key == "github_ecosystem_scout":
        gs = signals.get("github_scout") or {}
        count = int(gs.get("new_candidates_count") or 0)
        msg = gs.get("user_message_zh") or ""
        top = gs.get("top_new") or []
        if count and top:
            repos = "、".join(f"{t.get('repo')}({t.get('stars')}★)" for t in top[:3])
            finding = f"{msg} 本轮新发现：{repos}。"
        elif msg:
            finding = msg
        else:
            finding = (
                "【GitHub 生态侦察】研究员将按 catalog 缺口自动搜索 GitHub，"
                "结果写入 Hermes Inbox；您无需亲自翻找 repo。"
            )
        evidence.append({"type": "github_scout", "ref": "new_candidates_count", "value": count})
        if top:
            evidence.append({"type": "github_scout", "ref": "top_new", "value": top[:3]})
        impact = "high" if count >= 3 else "medium" if count else "low"

    else:
        pending = signals.get("gw_pending_p0") or []
        lane_match = [t for t in pending if t.get("lane") == topic.get("lane")]
        if lane_match:
            t0 = lane_match[0]
            finding = f"【{topic['label']}】关联待办 {t0.get('id')}：{t0.get('title')}。建议经 PM  inbox 排期，不自动改代码。"
            evidence.append({"type": "gw_task", "ref": t0.get("id"), "value": t0.get("status")})
            impact = "medium"
        else:
            finding = (
                f"【{topic['label']}】本小时无 P0 积压信号；维持只读研究节奏，"
                "输出供营销/销售专家人工采纳。"
            )
            impact = "low"

    return finding, evidence, impact


def _suggested_tasks(topic: dict[str, str], signals: dict[str, Any]) -> list[dict[str, str]]:
    """_suggested_tasks。

    参数说明：
    :param topic: 参数 topic
    :param signals: 参数 signals
    :return: 返回处理结果。
    """
    lane = topic.get("lane") or "GW-PM"
    pending = [t for t in signals.get("gw_pending_p0") or [] if t.get("lane") == lane]
    out: list[dict[str, str]] = []
    for t in pending[:2]:
        out.append({"id_hint": t.get("id") or "", "title": t.get("title") or "", "lane": lane})
    if not out and lane == "GW-R":
        out.append(
            {
                "id_hint": "GW-R-AGENT-02",
                "title": "ResearchBrief 经 ECC+PM 门控入登记册",
                "lane": "GW-R",
            }
        )
    return out


def compose_research_brief(
    db: Session | None,
    *,
    topic: dict[str, str] | None = None,
    signals: dict[str, Any] | None = None,
    at: datetime | None = None,
) -> dict[str, Any]:
    """compose_research_brief。

    参数说明：
    :param db: 参数 db
    :param topic: 参数 topic
    :param signals: 参数 signals
    :param at: 参数 at
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    now = at or datetime.now(timezone.utc)
    topic = topic or hourly_topic(at=now)
    signals = signals if signals is not None else collect_signals(db)
    finding, evidence, impact = _compose_finding(topic, signals)
    fp = _brief_fingerprint(topic["key"], finding)
    brief_id = f"{now.strftime('%Y%m%d%H')}:{topic['key']}:{fp[:8]}"
    return {
        "brief_id": brief_id,
        "topic_key": topic["key"],
        "topic_label": topic["label"],
        "lane": topic["lane"],
        "category": topic.get("category", "paper"),
        "finding": finding,
        "evidence": evidence,
        "impact": impact,
        "confidence": "high" if len(evidence) >= 2 else "medium" if evidence else "low",
        "suggested_tasks": _suggested_tasks(topic, signals),
        "forbidden_auto_actions": [
            "code_merge",
            "config_mutate",
            "send_email",
            "publish_post",
            "auto_enqueue_deerflow",
        ],
        "constitution_version": CONSTITUTION_VERSION,
        "generated_at": now.isoformat(),
        "fingerprint": fp,
    }


def _dedupe_hit(fingerprint: str) -> bool:
    """_dedupe_hit。

    参数说明：
    :param fingerprint: 参数 fingerprint
    :return: 返回处理结果。
    """
    if not redis_client:
        return False
    key = f"{BRIEF_DEDUPE_PREFIX}{fingerprint}"
    if redis_client.get(key):
        return True
    redis_client.set(key, "1", ex=86400 * 3)
    return False


def save_brief_snapshot(brief: dict[str, Any]) -> dict[str, Any]:
    """save_brief_snapshot。

    参数说明：
    :param brief: 参数 brief
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    body = {**brief, "saved_at": datetime.now(timezone.utc).isoformat()}
    if redis_client:
        redis_client.set(BRIEF_SNAPSHOT_KEY, json.dumps(body, ensure_ascii=False), ex=86400 * 14)
    return body


def append_brief_inbox(brief: dict[str, Any], *, ecc_verdict: str, department_routing: list[dict]) -> None:
    """append_brief_inbox。

    参数说明：
    :param brief: 参数 brief
    :param ecc_verdict: 参数 ecc_verdict
    :param department_routing: 参数 department_routing
    :return: 返回处理结果。
    """
    assert_maintenance_action("write_patrol_snapshot")
    if not redis_client:
        return
    item = {
        "brief_id": brief.get("brief_id"),
        "topic_label": brief.get("topic_label"),
        "lane": brief.get("lane"),
        "impact": brief.get("impact"),
        "finding": (brief.get("finding") or "")[:500],
        "ecc_verdict": ecc_verdict,
        "departments": [d.get("seat") for d in department_routing],
        "suggested_tasks": brief.get("suggested_tasks") or [],
        "status": "pending_pm",
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    raw = redis_client.get(BRIEF_INBOX_KEY)
    inbox: list = []
    if raw:
        try:
            inbox = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            inbox = []
    inbox.insert(0, item)
    redis_client.set(BRIEF_INBOX_KEY, json.dumps(inbox[:INBOX_MAX], ensure_ascii=False), ex=86400 * 30)


def load_brief_snapshot() -> dict[str, Any] | None:
    """load_brief_snapshot。
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return None
    raw = redis_client.get(BRIEF_SNAPSHOT_KEY)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def load_brief_inbox(*, limit: int = 20) -> list[dict[str, Any]]:
    """load_brief_inbox。

    参数说明：
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return []
    raw = redis_client.get(BRIEF_INBOX_KEY)
    if not raw:
        return []
    try:
        items = json.loads(raw)
        return items[:limit] if isinstance(items, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def run_research_brief_cycle(
    db: Session | None,
    *,
    trigger: str = "scheduler",
    force: bool = False,
) -> dict[str, Any]:
    """单轮研究员：采集 → Brief → 去重；不写业务表、不发信。"""
    assert_maintenance_action("read_probe")
    topic = hourly_topic()
    signals = collect_signals(db)
    brief = compose_research_brief(db, topic=topic, signals=signals)
    try:
        from app.services.hermes.anysearch_probe_service import enrich_brief_with_anysearch
        brief = enrich_brief_with_anysearch(brief)
        fp = _brief_fingerprint(brief["topic_key"], brief["finding"])
        brief["fingerprint"] = fp
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        brief["brief_id"] = f"{stamp}:{brief['topic_key']}:{fp[:8]}"
    except Exception as exc:
        logger.warning("AnySearch enrich skipped: %s", exc)

    skipped = False
    if not force and _dedupe_hit(brief["fingerprint"]):
        skipped = True
        prev = load_brief_snapshot()
        return {
            "trigger": trigger,
            "skipped": True,
            "reason": "duplicate_fingerprint",
            "topic_key": topic["key"],
            "previous_brief_id": (prev or {}).get("brief_id"),
        }

    saved = save_brief_snapshot(brief)
    logger.info(
        "Research brief [%s] topic=%s impact=%s id=%s",
        trigger,
        topic["key"],
        brief.get("impact"),
        brief.get("brief_id"),
    )
    return {
        "trigger": trigger,
        "skipped": skipped,
        "brief": saved,
        "signals_summary": {
            "gw_pending_p0": signals.get("gw_pending_p0_count"),
            "patrol_fail": (signals.get("patrol_summary") or {}).get("fail_count"),
        },
    }
