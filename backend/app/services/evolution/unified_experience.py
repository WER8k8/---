# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P2-1 经验双源统一 — 唯一真源 = Evolution PG（ExperienceStore / EvolutionTaskRecord）。

红线：
    · hermes JSON 经验文件不再是 planner 主真源（可作本地兜底只读）
    · 读失败诚实空列表，不编造经验
    · 每条 hint 带 source=evolution_pg / json_fallback
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

SOURCE_PG = "evolution_pg"
SOURCE_JSON = "json_fallback"


def _safe_db(db: Any) -> Any:
    if db is None:
        return None
    if type(db).__name__ in ("Depends", "DependsObject"):
        return None
    if not hasattr(db, "query") and not hasattr(db, "execute"):
        return None
    return db


def fetch_experience_hints(
    db: Any,
    *,
    tenant_id: str = "",
    scene_type: str = "",
    limit: int = 5,
    allow_json_fallback: bool = True,
) -> list[dict[str, Any]]:
    """统一读经验：优先 Evolution PG；无库/无数据时可选 JSON 兜底（标注 source）。"""
    session = _safe_db(db)
    hints: list[dict[str, Any]] = []
    if session is not None:
        try:
            from app.services.evolution.experience_store import ExperienceStore
            store = ExperienceStore(session)
            experiences = store.find_applicable(
                tenant_id=tenant_id or "",
                scene_type=scene_type or "",
                limit=limit,
            )
            for e in experiences[:limit]:
                if not isinstance(e, dict):
                    continue
                hints.append({
                    "id": e.get("id"),
                    "type": e.get("experience_type") or e.get("task_type") or scene_type,
                    "summary": e.get("summary") or e.get("description") or "",
                    "score": e.get("success_score", 0) or e.get("confidence", 0),
                    "source": SOURCE_PG,
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug("ExperienceStore 读取失败: %s", exc)

        # 获客事件（win/loss）补强：evolution_task_records
        try:
            from sqlalchemy import or_
            from app.models.evolution import EvolutionTaskRecord
            q = session.query(EvolutionTaskRecord).filter(
                or_(
                    EvolutionTaskRecord.task_type.like("acquisition.ops_%"),
                    EvolutionTaskRecord.task_type.like("acquisition.%"),
                )
            )
            if tenant_id:
                try:
                    q = q.filter(EvolutionTaskRecord.tenant_id == tenant_id)
                except Exception:
                    pass
            rows = q.order_by(EvolutionTaskRecord.created_at.desc()).limit(limit).all()
            for r in rows:
                tid = str(getattr(r, "task_type", "") or "")
                if tid.startswith("acquisition.ops_win"):
                    summary = "历史成交：优先确认交期/认证/付款安全"
                    score = 0.9
                elif tid.startswith("acquisition.ops_loss"):
                    summary = f"历史流失：{(getattr(r, 'output_summary', '') or '')[:120]}"
                    score = 0.2
                else:
                    summary = str(getattr(r, "output_summary", "") or tid)[:120]
                    score = 0.5 if getattr(r, "success", True) else 0.2
                hints.append({
                    "id": str(getattr(r, "id", "")),
                    "type": tid,
                    "summary": summary,
                    "score": score,
                    "source": SOURCE_PG,
                })
        except Exception as exc:  # noqa: BLE001
            logger.debug("acquisition 经验补强失败: %s", exc)

    if not hints and allow_json_fallback:
        try:
            from app.services.hermes.experience_engine import ExperienceEngine
            eng = ExperienceEngine()
            scene = (scene_type or "").strip()
            if scene:
                for r in eng.query(scene, top_k=limit):
                    hints.append({
                        "id": r.get("timestamp"),
                        "type": r.get("task_type"),
                        "summary": r.get("solution_summary") or "",
                        "score": 1.0 if r.get("success") else 0.0,
                        "source": SOURCE_JSON,
                    })
        except Exception:
            pass
    return hints[:limit]


def experience_source_report(db: Any, tenant_id: str = "") -> dict[str, Any]:
    """体检：当前真源状态（供作战台/运维看）。"""
    session = _safe_db(db)
    report: dict[str, Any] = {
        "primary_source": SOURCE_PG,
        "pg_available": False,
        "pg_hints": 0,
        "json_fallback_used": False,
        "tenant_id": tenant_id,
        "plain_summary": "",
        "hint": "唯一真源=进化 PG；JSON 仅本地兜底且标注 source=json_fallback。",
    }
    if session is not None:
        try:
            from app.models.evolution import EvolutionTaskRecord
            n = session.query(EvolutionTaskRecord).filter(
                EvolutionTaskRecord.task_type.like("acquisition.%")
            ).count()
            report["pg_available"] = True
            report["pg_hints"] = int(n or 0)
            report["plain_summary"] = (
                f"经验真源=PG，获客相关记录 {n} 条。"
                if n
                else "经验真源=PG，暂无获客记录（会在成交/流失后增长）。"
            )
            return report
        except Exception as exc:  # noqa: BLE001
            report["plain_summary"] = f"PG 读取异常，已降级 JSON 兜底：{str(exc)[:80]}"
            report["json_fallback_used"] = True
            return report
    report["plain_summary"] = "无数据库会话，经验读取降级 JSON 兜底（非生产口径）。"
    report["json_fallback_used"] = True
    return report
