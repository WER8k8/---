# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199304817). All rights reserved.
"""贸易情报刷新路由（`/ops/trade-intel/status` · `/ops/trade-intel/refresh`）。

接线背景（2026-09-24 缺失接口逐个修复）：
    前端 `views/admin/ai-engine/trade-intel.vue`：
      · `loadRefreshStatus()`  → GET  `/api/v1/ops/trade-intel/status`，读 `data.latest`
      · `runComtradeRefresh()` → POST `/api/v1/ops/trade-intel/refresh`，读 `data.rows_updated`
    两条在 openapi 中零命中 → 页面「最近刷新」永远为空、刷新按钮必失败。

数据来源（真实能力，非编造）：
    · status  ← `trade_intel_refresh_service.load_refresh_snapshot()`（读落盘快照文件）
    · refresh ← `trade_intel_refresh_service.refresh_customs_from_comtrade()`
                （真抓 UN Comtrade；失败品类保留上一版数值，不伪造成功）
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.trade_intel_refresh_service import (
    load_refresh_snapshot,
    refresh_customs_from_comtrade,
)

logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/ops"
ROUTE_TAGS = ["运维聚合"]

router = APIRouter(tags=["运维聚合"])


@router.get("/trade-intel/status")
def ops_trade_intel_status(current_user: User = Depends(get_current_user)):
    """最近一次 Comtrade 刷新快照（无快照时 latest=null，不伪造）。"""
    return success_response(data={"latest": load_refresh_snapshot()})


@router.post("/trade-intel/refresh")
def ops_trade_intel_refresh(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发一次 Comtrade 海关数据刷新（同步执行；失败品类保留上一版数值）。

    求真：返回体带 `rows_updated` / `errors`，失败不掩盖。
    """
    try:
        result = refresh_customs_from_comtrade(db=db, trigger="manual")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Comtrade 刷新失败")
        return error_response(500, f"Comtrade 刷新失败：{type(exc).__name__}: {exc}")
    return success_response(data=result)
