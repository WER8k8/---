# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-10 旺财线B：建站卡壳 → 调获客/小图补救（禁复读）。

规则：
    · 只对 failed/timeout 的建站/内容任务触发
    · 同一 tenant+issue 短窗内只派一次（幂等 key）
    · 调 acquisition dispatch 小图或输出可执行下一步，不重复念同一段话
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

_recent: dict[str, float] = {}
_COOLDOWN_SEC = 600  # 10 分钟内同 key 不复读/不重派


def _key(tenant_id: str, issue: str) -> str:
    return f"{tenant_id or 'demo'}|{issue}"


def detect_site_blockers(db: Any, *, tenant_id: str = "", limit: int = 5) -> list[dict[str, Any]]:
    """从 ai_tasks 找建站/内容失败任务（诚实：无库返回空）。"""
    if db is None or not hasattr(db, "query"):
        return []
    try:
        from sqlalchemy import or_
        from app.models.ai_task import AiTask
        q = db.query(AiTask).filter(
            AiTask.status.in_(["failed", "timeout"]),
            or_(
                AiTask.task_type.ilike("%site%"),
                AiTask.task_type.ilike("%content%"),
                AiTask.task_type.ilike("%publish%"),
                AiTask.task_type.ilike("%wangcai%"),
            ),
        )
        try:
            if tenant_id and hasattr(AiTask, "tenant_id"):
                from app.services.acquisition.repo import resolve_tenant_uuid
                tid = resolve_tenant_uuid(db, tenant_id) or tenant_id
                q = q.filter(AiTask.tenant_id == tid)
        except Exception:
            pass
        rows = q.order_by(AiTask.created_at.desc()).limit(limit).all()
        out = []
        for t in rows:
            out.append({
                "task_id": str(getattr(t, "id", "")),
                "task_type": str(getattr(t, "task_type", "") or ""),
                "status": str(getattr(t, "status", "") or ""),
                "error": str(getattr(t, "error_message", "") or "")[:200],
            })
        return out
    except Exception as exc:  # noqa: BLE001
        logger.debug("detect_site_blockers 失败: %s", exc)
        return []


def rescue_plan(
    *,
    tenant_id: str = "demo",
    blockers: Optional[list[dict[str, Any]]] = None,
    db: Any = None,
) -> dict[str, Any]:
    """建站卡壳补救：小图建议 + 是否允许派发 + 禁复读标记。"""
    blockers = list(blockers if blockers is not None else detect_site_blockers(db, tenant_id=tenant_id))
    if not blockers:
        return {
            "tenant_id": tenant_id,
            "blocked": False,
            "blockers": [],
            "suggested_intent": "",
            "allow_dispatch": False,
            "repeated": False,
            "plain_summary": "未发现建站/内容卡壳，无需补救。",
            "next_steps": [],
            "hint": "旺财线B：卡壳才触发，不刷屏。",
        }

    top = blockers[0]
    issue = top.get("task_type") or top.get("error") or "site_block"
    k = _key(tenant_id, issue)
    now = time.time()
    last = _recent.get(k, 0)
    repeated = bool(last and (now - last) < _COOLDOWN_SEC)
    if not repeated:
        _recent[k] = now

    # 建站卡壳 → 用获客/内容小图，而不是复读建站失败原因
    if "content" in issue or "publish" in issue:
        suggested = "content_acquisition"
        steps = ["检查内容引擎配置", "改走获客词典 route-content-inquiry", "人工确认后再派发"]
    else:
        suggested = "generate_site"
        steps = [
            "核对建站节点失败原因（不重复念同一段报错）",
            "可改派小图：find_leads 拓客补流量（先看词典）",
            "外发/发布节点必须人审",
        ]

    return {
        "tenant_id": tenant_id,
        "blocked": True,
        "blockers": blockers,
        "suggested_intent": suggested,
        "alternate_intent": "find_leads" if suggested == "generate_site" else "inquiry_reply",
        "allow_dispatch": not repeated,
        "repeated": repeated,
        "plain_summary": (
            f"发现 {len(blockers)} 个建站/内容卡壳。"
            + ("近期已提醒过，本次不重复派发（防复读）。" if repeated else "可一键派发小图补救。")
        ),
        "next_steps": steps,
        "hint": "禁复读：同问题 10 分钟内只提醒/只派一次。",
        "dictionary_ref": "docs/compose/orchestration-dictionary-v1.yaml",
    }
