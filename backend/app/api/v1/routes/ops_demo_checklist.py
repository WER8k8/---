# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199304817). All rights reserved.
"""彩排清单路由（`/ops/demo-checklist`）。

接线背景（2026-09-24 缺失接口逐个修复）：
    前端 `views/admin/demo-rehearsal.vue:780` 在 fetch `/api/v1/ops/demo-checklist`，
    期望 `data.steps[] / data.readiness / data.recording_hint`，
    但全仓无路由定义 → 404 → 页面彩排清单永远为空。

数据来源（均为真实能力，非编造）：
    · steps     ← `pilot_rehearsal_service._ops_checklist()`（现有 5 条运营核对项）
    · readiness ← `production_readiness_service.run_readiness_checks(db)`
    · recording_hint 不返回 —— 前端已有默认文案，后端不重复造 UI 文案
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.pilot_rehearsal_service import _ops_checklist
from app.services.production_readiness_service import run_readiness_checks

logger = logging.getLogger(__name__)

ROUTE_PREFIX = "/ops"
ROUTE_TAGS = ["运维聚合"]

router = APIRouter(tags=["运维聚合"])


@router.get("/demo-checklist")
def ops_demo_checklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """彩排/送检用的运营核对清单 + 就绪度快照。

    求真：steps 来自 pilot_rehearsal_service 的既有清单；readiness 来自真实探测。
    不返回 recording_hint（UI 文案由前端持有），前端会走其默认值。
    """
    try:
        steps = _ops_checklist()
        readiness = run_readiness_checks(db).to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.exception("彩排清单生成失败")
        return error_response(500, f"彩排清单生成失败：{type(exc).__name__}: {exc}")
    return success_response(data={"steps": steps, "readiness": readiness})
