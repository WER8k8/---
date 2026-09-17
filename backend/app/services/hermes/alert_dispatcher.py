# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 运维告警 — 飞书 Webhook（巡站 / 技术雷达 / 异常）。"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.core.cache import redis_client
from app.services.hermes.maintenance_constitution import assert_maintenance_action

logger = logging.getLogger("uj-admin.hermes_alert")

DEDUPE_PREFIX = "hermes:alert:sent:"


def _webhook_url(override: str | None = None) -> str:
    """_webhook_url。

    参数说明：
    :param override: 参数 override
    :return: 返回处理结果。
    """
    return (
        (override or "").strip()
        or os.getenv("HERMES_ALERT_WEBHOOK_URL", "").strip()
        or os.getenv("OPS_READINESS_WEBHOOK_URL", "").strip()
        or (settings.FEISHU_WEBHOOK_URL or "").strip()
    )


def _dedupe_key(event_type: str, fingerprint: str) -> str:
    """_dedupe_key。

    参数说明：
    :param event_type: 参数 event_type
    :param fingerprint: 参数 fingerprint
    :return: 返回处理结果。
    """
    raw = f"{event_type}:{fingerprint}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{DEDUPE_PREFIX}{digest}"


def should_send_alert(event_type: str, fingerprint: str, cooldown_minutes: int | None = None) -> bool:
    """should_send_alert。

    参数说明：
    :param event_type: 参数 event_type
    :param fingerprint: 参数 fingerprint
    :param cooldown_minutes: 参数 cooldown_minutes
    :return: 返回处理结果。
    """
    assert_maintenance_action("read_probe")
    if not redis_client:
        return True
    minutes = cooldown_minutes
    if minutes is None:
        minutes = int(getattr(settings, "HERMES_ALERT_COOLDOWN_MINUTES", 60) or 60)
    key = _dedupe_key(event_type, fingerprint)
    if redis_client.get(key):
        return False
    return True


def mark_alert_sent(event_type: str, fingerprint: str, cooldown_minutes: int | None = None) -> None:
    """mark_alert_sent。

    参数说明：
    :param event_type: 参数 event_type
    :param fingerprint: 参数 fingerprint
    :param cooldown_minutes: 参数 cooldown_minutes
    :return: 返回处理结果。
    """
    assert_maintenance_action("emit_alert")
    if not redis_client:
        return
    minutes = cooldown_minutes
    if minutes is None:
        minutes = int(getattr(settings, "HERMES_ALERT_COOLDOWN_MINUTES", 60) or 60)
    key = _dedupe_key(event_type, fingerprint)
    redis_client.set(key, datetime.now(timezone.utc).isoformat(), ex=max(minutes, 5) * 60)


def send_feishu_card(
    *,
    title: str,
    body_md: str,
    template: str = "red",
    webhook_url: str | None = None,
    event_type: str = "hermes_ops",
    fingerprint: str = "",
    respect_cooldown: bool = True,
) -> dict[str, Any]:
    """发送飞书交互卡片；默认冷却去重。"""
    assert_maintenance_action("emit_alert")
    url = _webhook_url(webhook_url)
    if not url:
        return {"sent": False, "reason": "no_webhook_configured"}

    fp = fingerprint or hashlib.sha256(f"{title}\n{body_md}".encode()).hexdigest()[:12]
    if respect_cooldown and not should_send_alert(event_type, fp):
        return {"sent": False, "reason": "cooldown", "fingerprint": fp}

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title[:120]},
                "template": template,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": body_md[:4000]},
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "Hermes 仅自动执行安全探测/缓存刷新；改代码/发版/删数据请在本群回复或 Admin 运维页下指令。",
                        }
                    ],
                },
            ],
        },
    }
    try:
        with httpx.Client(timeout=12) as client:
            resp = client.post(url, json=payload)
        ok = resp.status_code < 400
        if ok and respect_cooldown:
            mark_alert_sent(event_type, fp)
        return {
            "sent": ok,
            "status_code": resp.status_code,
            "fingerprint": fp,
            "response": resp.text[:200] if not ok else "",
        }
    except Exception as exc:
        logger.warning("Hermes feishu alert failed: %s", exc)
        return {"sent": False, "reason": str(exc), "fingerprint": fp}


def _wechat_webhook_url() -> str:
    """_wechat_webhook_url。
    :return: 返回处理结果。
    """
    return (
        os.getenv("HERMES_WECHAT_WEBHOOK_URL", "").strip()
        or (getattr(settings, "HERMES_WECHAT_WEBHOOK_URL", "") or "").strip()
    )


def send_wechat_markdown(
    *,
    title: str,
    body_md: str,
    event_type: str = "hermes_ops",
    fingerprint: str = "",
    respect_cooldown: bool = True,
) -> dict[str, Any]:
    """企业微信机器人 Markdown；与飞书共用冷却指纹。"""
    assert_maintenance_action("emit_alert")
    url = _wechat_webhook_url()
    if not url:
        return {"sent": False, "reason": "no_wechat_webhook"}

    fp = fingerprint or hashlib.sha256(f"{title}\n{body_md}".encode()).hexdigest()[:12]
    if respect_cooldown and not should_send_alert(f"{event_type}:wechat", fp):
        return {"sent": False, "reason": "cooldown", "fingerprint": fp}

    try:
        from app.services.wecom_push_service import send_platform_ops_webhook
        result = send_platform_ops_webhook(title=title, body_md=body_md)
        ok = bool(result.get("sent"))
        if ok and respect_cooldown:
            mark_alert_sent(f"{event_type}:wechat", fp)
        return {"sent": ok, "fingerprint": fp, **result}
    except Exception as exc:
        logger.warning("Hermes wechat alert failed: %s", exc)
        return {"sent": False, "reason": str(exc), "fingerprint": fp}


def dispatch_ops_alert(
    *,
    title: str,
    body_md: str,
    template: str = "red",
    event_type: str = "hermes_ops",
    fingerprint: str = "",
) -> dict[str, Any]:
    """飞书 + 微信双通道（各自独立 Webhook，共用冷却键）。"""
    feishu = send_feishu_card(
        title=title,
        body_md=body_md,
        template=template,
        event_type=event_type,
        fingerprint=fingerprint,
    )
    wechat = send_wechat_markdown(
        title=title,
        body_md=body_md,
        event_type=event_type,
        fingerprint=fingerprint,
    )
    return {
        "sent": bool(feishu.get("sent") or wechat.get("sent")),
        "feishu": feishu,
        "wechat": wechat,
        "fingerprint": fingerprint or feishu.get("fingerprint"),
    }


def notify_patrol_report(report: dict[str, Any], *, remediation: dict[str, Any] | None = None) -> dict[str, Any]:
    """notify_patrol_report。

    参数说明：
    :param report: 参数 report
    :param remediation: 参数 remediation
    :return: 返回处理结果。
    """
    status = report.get("overall_status", "unknown")
    if status == "healthy":
        return {"sent": False, "reason": "healthy_skip"}

    fails = [p for p in report.get("probes") or [] if p.get("status") == "fail"]
    lines = [f"**整体**: {status} · 通过 {report.get('pass_count')} / 失败 {report.get('fail_count')}"]
    for p in fails[:6]:
        lines.append(f"- **{p.get('title')}**: {p.get('error') or p.get('message') or 'fail'}")
    for s in (report.get("suggestions") or [])[:4]:
        lines.append(f"- 建议: {s.get('suggestion')}")
    if remediation:
        lines.append(f"\n**自动处理**: {remediation.get('summary', '无')}")

    template = "red" if status == "critical" else "orange"
    fp = f"patrol:{status}:{report.get('fail_count')}:{report.get('saved_at', '')[:10]}"
    return dispatch_ops_alert(
        title=f"🛡 Hermes 巡站告警 · {status}",
        body_md="\n".join(lines),
        template=template,
        event_type="hermes_patrol",
        fingerprint=fp,
    )


def _format_expert_line(candidate: dict[str, Any]) -> str:
    """_format_expert_line。

    参数说明：
    :param candidate: 参数 candidate
    :return: 返回处理结果。
    """
    reviews = candidate.get("expert_reviews") or []
    if not reviews:
        return ""
    parts = [f"{r.get('display_name')}·{r.get('verdict')}" for r in reviews[:3]]
    rec = (reviews[0].get("recommendation") or "")[:60]
    return f"  **ECC专家**: {', '.join(parts)}\n  建议: {rec}\n"


def notify_tech_radar(report: dict[str, Any]) -> dict[str, Any]:
    """notify_tech_radar。

    参数说明：
    :param report: 参数 report
    :return: 返回处理结果。
    """
    candidates = report.get("candidates") or []
    flagged = [
        c
        for c in candidates
        if c.get("expert_verdict") == "fail"
        or c.get("impact") == "high"
        or c.get("hermes_action") == "notify_human_review"
    ]
    if not flagged and report.get("fetch_errors"):
        flagged = [
            {
                "title": "抓取异常",
                "url": "",
                "category": "unknown",
                "validation_status": "fail",
                "validation_note": str(report.get("fetch_errors")),
                "expert_verdict": "fail",
            }
        ]

    if not flagged:
        return {"sent": False, "reason": "no_notify_worthy"}

    lines = [
        f"**扫描模式**: {report.get('mode', 'fetch')}",
        f"**候选数**: {len(candidates)} · 专家否决 {report.get('expert_fail_count', 0)}",
        "",
        "**ECC 专家需你决策的项**:",
    ]
    for c in flagged[:5]:
        lines.append(
            f"- **{c.get('title')}** ({c.get('category')})\n"
            f"  探测: {c.get('validation_status')} · 专家: {c.get('expert_verdict', '—')}\n"
            f"{_format_expert_line(c)}"
            f"  {c.get('url', '')}"
        )
    lines.append(
        "\n指令: `full_cycle` / `rerun_tech_radar` / `ack`（Admin → Hermes 运维 或飞书跟进）"
    )
    fp = f"tech_radar:{len(flagged)}:{report.get('saved_at', '')[:10]}"
    return dispatch_ops_alert(
        title="📡 技术雷达 · ECC 专家评审",
        body_md="\n".join(lines),
        template="blue",
        event_type="hermes_tech_radar",
        fingerprint=fp,
    )


def notify_rank_guard(report: dict[str, Any]) -> dict[str, Any]:
    """SEO-05：Rank Guard 未通过时通知超管。"""
    blocked = report.get("blocked_reasons") or []
    warnings = report.get("warning_reasons") or []
    if not blocked and not warnings:
        return {"sent": False, "reason": "nothing_to_notify"}

    metrics = report.get("metrics") or {}
    lines = [
        f"**触发**: {report.get('trigger', 'probe')}",
        f"**SEO 审计分**: {metrics.get('seo_audit_score', '—')}",
        f"**GEO 收录率**: {metrics.get('geo_indexed_rate', '—')}",
        "",
        report.get("message") or "Rank Guard 未通过",
        "",
        "请在 **超管司令部 → GEO Rank Guard** 查看详情；发布前须人工确认。",
    ]
    fp = f"rank_guard:{','.join(blocked)}:{report.get('checked_at', '')[:10]}"
    return dispatch_ops_alert(
        title="🛡️ GEO Rank Guard 告警",
        body_md="\n".join(lines),
        template="red" if blocked else "orange",
        event_type="hermes_rank_guard",
        fingerprint=fp,
    )


def notify_inclusion_batch(report: dict[str, Any]) -> dict[str, Any]:
    """SEO-05：批量收录复检未收录比例过高时通知超管。"""
    not_inc = int(report.get("not_included_count") or 0)
    updated = int(report.get("updated_count") or 0)
    if not_inc < 3:
        return {"sent": False, "reason": "below_threshold"}
    lines = [
        f"**复检条数**: {updated}",
        f"**未收录**: {not_inc} · **已收录**: {report.get('included_count', 0)}",
        f"**探测模式**: {report.get('probe_modes') or {}}",
        "",
        "样本：",
    ]
    for s in (report.get("samples") or [])[:5]:
        flag = "✅" if s.get("included") else "❌"
        lines.append(f"- {flag} {s.get('url', '')[:80]}")
    lines.append("\n请在 SEO 矩阵 → 收录监控 或司令部复检。")
    fp = f"inclusion:{not_inc}:{report.get('checked_at', '')[:10]}"
    return dispatch_ops_alert(
        title="📉 SEO 收录复检告警",
        body_md="\n".join(lines),
        template="orange",
        event_type="hermes_inclusion",
        fingerprint=fp,
    )
