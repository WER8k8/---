"""旺财统一入口 — 公开站与开户向导必须同源。

V1.9+：WangcaiRouter 总编排接入（阶段 1，不依赖 LLM）：
- 新意图（规格/认证/价格/运费/公司/案例/转人工）走租户知识管线；
- 旧意图（海关/蓝海/出口可行性/帮助）与任何异常 → 旧引擎降级路径（零回归）；
- 特性开关 WANGCAI_ROUTER_ENABLED=0 可整体回退旧引擎。
"""

from __future__ import annotations

import logging
import os
from typing import Any, TYPE_CHECKING

from app.services.tenant_product_context import WANGCAI_ENGINE, resolve_tenant_product_hint
from app.services.wangcai_trade_service import ask_wangcai

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


def _router_enabled() -> bool:
    """_router_enabled。
    :return: 返回处理结果。
    """
    return os.environ.get("WANGCAI_ROUTER_ENABLED", "1") != "0"


def ask_wangcai_for_tenant(
    db: Session,
    tenant: Tenant,
    message: str,
    *,
    source: str,
    product_hint_override: str | None = None,
    language: str | None = None,
    visitor_ref: str | None = None,
) -> dict[str, Any]:
    """
    唯一旺财调用点（公开 / 向导 / autopilot）。
    source: public_site | onboarding_chain | onboarding_autopilot
    visitor_ref: 可选；未提供时用 source+tenant 兼容兜底（前端访客标识接线为后续项）。
    """
    hint = (product_hint_override or "").strip() or resolve_tenant_product_hint(tenant)
    # ---- Router 优先（阶段 1 新意图知识管线）；任何异常/委托 → 旧引擎降级 ----
    if _router_enabled():
        try:
            from app.services.wangcai.router import get_router
            routed = get_router(db).handle(
                message,
                tenant_id=str(tenant.id),
                visitor_ref=visitor_ref or f"{source}:{tenant.id}",
                tenant_hint=hint,
                language=language,
            )
        except Exception:  # noqa: BLE001 — 公开挂件入口不得抛错，降级旧引擎
            logger.exception("wangcai router 异常，降级旧引擎")
            routed = None
        if routed:
            return {
                **routed,
                "wangcai_meta": {
                    "engine": "wangcai-router-v1",
                    "source": source,
                    "product_hint": hint,
                    "tenant_id": str(tenant.id),
                    "tenant_domain": tenant.domain,
                },
            }

    # ---- 旧引擎降级路径（零回归）----
    result = ask_wangcai(message, product_hint=hint, db=db, language=language)
    out = {**result, "wangcai_meta": {
        "engine": WANGCAI_ENGINE,
        "source": source,
        "product_hint": hint,
        "tenant_id": str(tenant.id),
        "tenant_domain": tenant.domain,
    }}
    return out
