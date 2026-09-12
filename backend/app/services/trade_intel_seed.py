"""将 M0 内置矩阵写入 trade_country_category（幂等）。"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.trade_intel import TradeCountryCategory
from app.services.trade_intel_data import load_trade_matrix


def seed_trade_matrix(db: Session) -> dict:
    """seed_trade_matrix。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    created = 0
    updated = 0
    for row in load_trade_matrix():
        for country_code, info in row["countries"].items():
            existing = (
                db.query(TradeCountryCategory)
                .filter(
                    TradeCountryCategory.category_key == row["category_key"],
                    TradeCountryCategory.country_code == country_code,
                )
                .first()
            )
            payload = {
                "category_label": row["category_label"],
                "hs_chapter": row["hs_chapter"],
                "verdict": info["verdict"],
                "growth": info.get("growth"),
                "competition": info.get("competition"),
                "certs_json": json.dumps(info.get("certs") or [], ensure_ascii=False),
                "notes": info.get("notes"),
                "is_active": True,
            }
            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(
                    TradeCountryCategory(
                        category_key=row["category_key"],
                        country_code=country_code,
                        **payload,
                    )
                )
                created += 1
    db.commit()
    return {"created": created, "updated": updated, "total_rows": created + updated}
