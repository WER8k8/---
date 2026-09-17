# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""P1-10：40 平台 catalog 与 DB 对齐检查。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.content import Platform
from app.services.platform_catalog import (
    PLATFORMS_CN,
    PLATFORMS_GLOBAL,
    all_catalog_rows,
    catalog_summary,
    upsert_platforms,
)


def alignment_report(db: Session) -> dict:
    """alignment_report。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    summary = catalog_summary(db)
    catalog_names = {row[0] for row in all_catalog_rows()}
    db_names = {p.name for p in db.query(Platform.name).all()}
    missing_in_db = sorted(catalog_names - db_names)
    extra_in_db = sorted(db_names - catalog_names)
    return {
        "summary": summary,
        "catalog_total": len(catalog_names),
        "db_total": len(db_names),
        "missing_in_db": missing_in_db[:30],
        "missing_count": len(missing_in_db),
        "extra_in_db": extra_in_db[:30],
        "extra_count": len(extra_in_db),
        "aligned": not missing_in_db and summary.get("ready"),
        "pm_table": {
            "cn": [n for n, *_ in PLATFORMS_CN],
            "global": [n for n, *_ in PLATFORMS_GLOBAL],
        },
    }


def seed_full_platforms(db: Session) -> dict:
    """seed_full_platforms。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    stats = upsert_platforms(db, all_catalog_rows())
    report = alignment_report(db)
    return {"seed": stats, "alignment": report}
