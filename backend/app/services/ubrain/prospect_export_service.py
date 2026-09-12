"""采购商候选导出 — CSV（人工核实后跟进）。"""

from __future__ import annotations

import csv
import io
from typing import Any

from sqlalchemy.orm import Session

from app.models.ubrain_accio import BuyerProspectLead


def export_prospects_csv(db: Session, tenant_id: str, *, limit: int = 500) -> str:
    """export_prospects_csv。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param limit: 参数 limit
    :return: 返回处理结果。
    """
    rows = (
        db.query(BuyerProspectLead)
        .filter(BuyerProspectLead.tenant_id == tenant_id)
        .order_by(BuyerProspectLead.created_at.desc())
        .limit(limit)
        .all()
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "title",
            "region",
            "country_code",
            "buyer_type",
            "fit_score",
            "status",
            "verification_status",
            "suggested_channel",
            "has_draft",
            "created_at",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.title,
                r.region_label,
                r.country_code or "",
                r.buyer_type,
                r.fit_score,
                r.status,
                "待核实候选",
                r.suggested_channel or "",
                "yes" if r.outreach_draft else "no",
                r.created_at.isoformat() if r.created_at else "",
            ]
        )
    return buf.getvalue()


def mark_prospect_contacted(
    db: Session,
    *,
    tenant_id: str,
    prospect_id: str,
    note: str | None = None,
) -> dict[str, Any]:
    """mark_prospect_contacted。

    参数说明：
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param prospect_id: 参数 prospect_id
    :param note: 参数 note
    :return: 返回处理结果。
    """
    row = (
        db.query(BuyerProspectLead)
        .filter(
            BuyerProspectLead.id == prospect_id,
            BuyerProspectLead.tenant_id == tenant_id,
        )
        .first()
    )
    if not row:
        raise ValueError("prospect_not_found")
    row.status = "contacted"
    if note:
        row.notes = ((row.notes or "") + "\n" + note.strip())[:2000]
    db.commit()
    return {
        "id": row.id,
        "status": row.status,
        "verification_status": "已联系待回复",
    }
