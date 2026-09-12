"""Client「今日三步」状态 — 填产品 → 发内容 → 看询盘。"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.tenant import Tenant


def build_today_three_payload(db: Session, tenant: Tenant) -> dict[str, Any]:
    """build_today_three_payload。

    参数说明：
    :param db: 参数 db
    :param tenant: 参数 tenant
    :return: 返回处理结果。
    """
    from app.models.inquiry import Inquiry
    from app.models.product import Product
    from app.services.inquiry_weekly_service import build_inquiry_weekly_report
    from app.services.tenant_product_profile_service import get_tenant_product_profile
    tid = str(tenant.id)
    product_count = db.query(Product).filter(Product.is_active).count()
    profile = get_tenant_product_profile(db, tid)
    has_product = product_count > 0 or bool(profile.get("primary_product"))
    publish_in_progress = 0
    publish_success = 0
    try:
        from app.models.content import PlatformAccount, PublishTask
        pub_q = (
            db.query(PublishTask)
            .join(PlatformAccount, PublishTask.account_id == PlatformAccount.id)
            .filter(PlatformAccount.tenant_id == tid)
        )
        publish_in_progress = pub_q.filter(
            PublishTask.status.in_(("pending", "processing"))
        ).count()
        publish_success = pub_q.filter(PublishTask.status == "success").count()
    except Exception:
        pass

    has_content_action = publish_success > 0 or publish_in_progress > 0
    weekly = build_inquiry_weekly_report(db, tenant)
    pending_all = weekly.get("all_pending", 0)
    steps = [
        {
            "id": "product",
            "order": 1,
            "title": "填好产品",
            "subtitle": "写清品名、规格、产地（大城/河间）",
            "done": has_product,
            "route": "/client/products",
            "cta": "去产品库" if not has_product else "完善产品",
            "hint": "可先导入产业带候选再改规格" if not has_product else "可继续从「产业带候选」补品类",
            "alt_route": "/client/product-candidates",
        },
        {
            "id": "content",
            "order": 2,
            "title": "发一批内容",
            "subtitle": "中文片加英文字幕，发到平台让人看见",
            "done": has_content_action,
            "route": "/client/video-overseas",
            "cta": "中文片出海" if not has_content_action else "继续发布",
            "hint": "上传车间实拍，一键出英文字幕再分发",
        },
        {
            "id": "inquiry",
            "order": 3,
            "title": "看询盘回电话",
            "subtitle": "外文自动变中文，你回中文出英文草稿",
            "done": weekly.get("followed", 0) > 0 and pending_all == 0,
            "route": "/client/inquiries",
            "cta": "去询盘列表",
            "hint": f"本周来了 {weekly.get('received', 0)} 条，待处理 {pending_all} 条",
        },
    ]
    done_count = sum(1 for s in steps if s["done"])
    next_step = next((s for s in steps if not s["done"]), steps[-1])
    return {
        "steps": steps,
        "done_count": done_count,
        "total_steps": len(steps),
        "next_step_id": next_step["id"],
        "next_route": next_step["route"],
        "product_count": product_count,
        "product_profile_ready": bool(profile.get("ready_for_outreach")),
        "region_label": profile.get("region_label_zh"),
        "weekly_inquiries": weekly,
        "headline": (
            "今天三步都完成了，继续保持！"
            if done_count >= 3
            else f"今天先做：{next_step['title']}"
        ),
    }
