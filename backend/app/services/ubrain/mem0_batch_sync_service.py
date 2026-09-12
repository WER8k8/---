"""INT-03：Mem0 洞察批量双写（超管触发 · 未配置则 no-op）。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_commercial_os import UbrainResearchInsight
from app.services.ubrain.flywheel_integrations import sync_insight_to_mem0


def sync_recent_insights_to_mem0(db: Session, *, limit: int = 25) -> dict[str, Any]:
    """sync_recent_insights_to_mem0。

    参数说明：
    :param db: 参数 db
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(UbrainResearchInsight)
        .order_by(UbrainResearchInsight.created_at.desc())
        .limit(limit)
        .all()
    )
    synced = 0
    skipped = 0
    errors: list[str] = []
    for row in rows:
        out = sync_insight_to_mem0(
            tenant_id=str(row.tenant_id),
            insight_id=str(row.id),
            intent=row.intent or "market_research",
            title=row.title or "",
            summary=row.summary or "",
            quality_score=row.quality_score,
        )
        if out.get("synced"):
            synced += 1
        elif out.get("reason") == "mem0_not_configured":
            skipped = len(rows)
            break
        else:
            skipped += 1
            errors.append(str(out.get("reason") or "failed")[:120])

    return {
        "total": len(rows),
        "synced": synced,
        "skipped": skipped,
        "errors_sample": errors[:5],
        "mem0_configured": synced > 0 or (len(rows) > 0 and skipped < len(rows)),
    }


def integrations_health_snapshot() -> dict[str, Any]:
    """integrations_health_snapshot。
    :return: 返回处理结果。
    """
    from app.services.geo.tavily_search import tavily_configured
    from app.services.ubrain.flywheel_integrations import flywheel_integrations_status
    base = flywheel_integrations_status()
    base["tavily_configured"] = tavily_configured()
    return base
