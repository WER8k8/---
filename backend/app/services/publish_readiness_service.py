"""发布就绪总览 — 建站 / IP 槽位 / 平台绑号，供内容分发中心使用。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.services.egress_quota_service import tenant_egress_summary
from app.services.onboarding_progress_service import _tenant_has_site
from app.services.platform_account_service import list_active_accounts
from app.services.video_bind_hub_service import build_video_bind_hub


async def build_publish_readiness(db: Session, *, tenant: Tenant) -> dict[str, Any]:
    """build_publish_readiness。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    tid = str(tenant.id)
    site_built = _tenant_has_site(tenant)
    egress = tenant_egress_summary(db, tenant)
    hub = await build_video_bind_hub(db, tenant_id=tid)
    accounts = list_active_accounts(db, tenant_id=tid)
    bound_accounts = sum(
        1 for a in accounts if (a.login_status or "") in ("logged_in", "bound")
    )
    video_summary = hub.get("summary") or {}
    video_bound = int(video_summary.get("bound_local") or 0)
    video_total = int(video_summary.get("video_platforms") or 0)
    next_actions: list[dict[str, str]] = []
    if not site_built:
        next_actions.append(
            {"id": "site", "label": "完成智能建站", "path": "/client/onboarding"}
        )
    if int(egress.get("quota") or 0) > 0 and int(egress.get("assigned_count") or 0) == 0:
        next_actions.append(
            {"id": "egress", "label": "申请静态 IP 槽位", "path": "/client/egress"}
        )
    if int(egress.get("remaining") or 0) > 0 and int(egress.get("assigned_count") or 0) > 0:
        pass
    elif int(egress.get("quota") or 0) > 0 and int(egress.get("remaining") or 0) == 0:
        next_actions.append(
            {"id": "egress_buy", "label": "加购海外 IP 槽位", "path": "/client/egress"}
        )
    if bound_accounts == 0 and video_bound == 0:
        next_actions.append(
            {
                "id": "bind",
                "label": "绑定发布平台（一次登录）",
                "path": "/client/distribute?focus=bind",
            }
        )
    elif video_bound < max(video_total, 1):
        next_actions.append(
            {
                "id": "bind_more",
                "label": f"继续绑号（已绑 {video_bound}/{video_total}）",
                "path": "/client/distribute?focus=bind",
            }
        )

    ready_to_publish = site_built and (bound_accounts > 0 or video_bound > 0)
    return {
        "site_built": site_built,
        "egress": egress,
        "video_bind": video_summary,
        "platform_accounts_bound": bound_accounts,
        "platform_accounts_total": len(accounts),
        "ready_to_publish": ready_to_publish,
        "next_actions": next_actions,
        "bind_disclaimer": (
            "视频短平台由平台为每个租户独占分配 AiToEarn 矩阵号代发（一客户一组号）；"
            "无需客户登录 AiToEarn。文章类平台可选自带号 OAuth/Cookie。"
        ),
        "quick_links": {
            "distribute": "/client/distribute",
            "video_bind": "/client/video-bind",
            "egress": "/client/egress",
            "publish_queue": "/client/queues/publish",
        },
    }
