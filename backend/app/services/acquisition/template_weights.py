# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-3 模板权重反哺 — 经验 → L1 航道权重建议（先只读，人审生效）。

原则：
    · 只出建议，不自动改调度
    · 成交多 → 权重上调；流失多 → 下调
    · 样本不足 → status=insufficient，不瞎调
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 基础权重与意图映射（与 planner L1 模板对齐）
INTENT_WEIGHTS: dict[str, dict[str, Any]] = {
    "find_leads": {"label": "主动拓客开发信", "base": 1.0},
    "fulfillment": {"label": "履约闭环", "base": 1.0},
    "whatsapp": {"label": "社媒/WhatsApp", "base": 0.9},
    "inquiry_reply": {"label": "询盘转化", "base": 1.0},
    "sample_followup": {"label": "样品跟进", "base": 0.8},
    "price_haggling": {"label": "议价换条件", "base": 0.8},
}

# 跟单阶段 → 偏向意图
_STAGE_INTENT = {
    "won": "fulfillment",
    "lost": "find_leads",
    "quoted": "find_leads",
    "sampling": "sample_followup",
    "negotiating": "price_haggling",
    "orchestrated": "fulfillment",
    "engaged": "inquiry_reply",
}

MIN_SAMPLES = 3


def _clamp_weight(v: float) -> float:
    return max(0.5, min(1.5, round(v, 2)))


def build_template_weight_suggestions(
    *,
    ops_store: Any = None,
    tenant_id: str = "",
    db: Any = None,
    dispatch_stats: Optional[dict[str, dict[str, Any]]] = None,
) -> dict[str, Any]:
    """汇总跟单结果 + 可选派发统计 → 每条航道的权重建议。"""
    won = 0
    lost = 0
    stage_counts: dict[str, int] = {}
    loss_reason_counts: dict[str, int] = {}

    if ops_store is not None:
        try:
            for card in getattr(ops_store, "_by_inquiry", {}).values():
                if tenant_id and getattr(card, "tenant_id", "") not in ("", tenant_id):
                    continue
                stage = (getattr(card, "stage", "") or "").lower()
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
                if stage == "won" or getattr(card, "won_at", ""):
                    won += 1
                if stage == "lost" or getattr(card, "loss_reasons", None):
                    lost += 1
                    for r in getattr(card, "loss_reasons", None) or []:
                        loss_reason_counts[r] = loss_reason_counts.get(r, 0) + 1
        except Exception as exc:  # noqa: BLE001
            logger.debug("ops_store 统计失败: %s", exc)

    # PG 经验补强（可选）
    pg_events = {"win": 0, "loss": 0, "dispatch_ok": 0, "dispatch_fail": 0}
    if db is not None:
        try:
            from sqlalchemy import or_
            from app.models.evolution import EvolutionTaskRecord
            rows = (
                db.query(EvolutionTaskRecord)
                .filter(EvolutionTaskRecord.task_type.like("acquisition.%"))
                .limit(500)
                .all()
            )
            for r in rows:
                t = str(getattr(r, "task_type", "") or "")
                if t.endswith("ops_win"):
                    pg_events["win"] += 1
                elif t.endswith("ops_loss"):
                    pg_events["loss"] += 1
                elif t.endswith("ops_dispatch"):
                    if getattr(r, "success", False):
                        pg_events["dispatch_ok"] += 1
                    else:
                        pg_events["dispatch_fail"] += 1
        except Exception:
            pass

    total_won = won + pg_events["win"]
    total_lost = lost + pg_events["loss"]
    total_outcome = total_won + total_lost
    win_rate = (total_won / total_outcome) if total_outcome else None

    suggestions = []
    for intent, meta in INTENT_WEIGHTS.items():
        base = float(meta.get("base") or 1.0)
        sample_n = 0
        delta = 0.0
        reasons: list[str] = []
        status = "ok"

        # 用 stage 粗归因到意图
        for stage, n in stage_counts.items():
            if _STAGE_INTENT.get(stage) == intent:
                sample_n += n
        if intent == "fulfillment":
            sample_n += pg_events["dispatch_ok"]
        if intent == "find_leads":
            sample_n += total_lost  # 拓客端丢单多 → 该航道需更严背调

        if win_rate is not None and total_outcome >= MIN_SAMPLES:
            if intent in ("fulfillment", "inquiry_reply"):
                if win_rate >= 0.6:
                    delta += 0.15
                    reasons.append(f"成交率 {win_rate:.0%}，建议提高该航道优先级")
                elif win_rate <= 0.2:
                    delta -= 0.15
                    reasons.append(f"成交率偏低 {win_rate:.0%}，建议降权并补背调")
            if intent == "find_leads" and total_lost >= MIN_SAMPLES:
                delta -= 0.1
                reasons.append("流失样本较多，建议开发信航道加强背调闸")
        if pg_events["dispatch_ok"] >= MIN_SAMPLES and intent == "fulfillment":
            delta += 0.05
            reasons.append("履约派发执行样本充足，可略提权重")
        if sample_n < MIN_SAMPLES and not reasons:
            status = "insufficient"
            reasons.append("样本不足，暂不建议调权")

        suggested = _clamp_weight(base + delta)
        suggestions.append({
            "intent": intent,
            "label": meta["label"],
            "base_weight": base,
            "suggested_weight": suggested,
            "delta": round(suggested - base, 2),
            "sample_n": sample_n,
            "status": status,
            "reasons": reasons,
            "applied": False,
            "requires_human_review": True,
        })

    top_loss = max(loss_reason_counts.items(), key=lambda x: x[1])[0] if loss_reason_counts else ""
    plain = (
        f"成交 {total_won} / 流失 {total_lost}。"
        + (f"最常见流失「{top_loss}」。" if top_loss else "")
        + "权重仅为建议，需人工确认后才会生效。"
    )
    return {
        "tenant_id": tenant_id,
        "won": total_won,
        "lost": total_lost,
        "win_rate": round(win_rate, 3) if win_rate is not None else None,
        "stage_counts": stage_counts,
        "loss_reason_counts": loss_reason_counts,
        "pg_events": pg_events,
        "suggestions": suggestions,
        "plain_summary": plain,
        "mode": "read_only_suggestions",
        "hint": "P2-3：经验 → L1 权重建议；未人审前调度仍用模板默认权重。",
    }


# 内存中的「已批准权重」（生产应落 PG；当前先只读建议 + 可选批准记录）
_approved: dict[str, dict[str, Any]] = {}


def approve_weight(tenant_id: str, intent: str, weight: float, approved_by: str = "operator") -> dict[str, Any]:
    """人审通过：记录批准权重（不自动改 planner 源码；供后续调度读取）。"""
    w = _clamp_weight(float(weight))
    _approved[f"{tenant_id or 'demo'}:{intent}"] = {
        "intent": intent,
        "weight": w,
        "approved_by": approved_by,
        "mode": "human_approved",
    }
    return dict(_approved[f"{tenant_id or 'demo'}:{intent}"])


def approved_weights(tenant_id: str = "") -> dict[str, Any]:
    prefix = f"{tenant_id or 'demo'}:"
    items = {k.split(":", 1)[1]: v for k, v in _approved.items() if k.startswith(prefix)}
    return {
        "tenant_id": tenant_id or "demo",
        "approved": items,
        "plain_summary": (
            f"已人审权重 {len(items)} 条。" if items else "暂无人审通过的权重，调度使用模板默认。"
        ),
    }
