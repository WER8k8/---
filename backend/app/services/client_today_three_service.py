# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Client「今日三步」状态 — 填产品 → 发内容 → 看询盘。数据只取真源，不注水。"""

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
            "title": "把产品放上去",
            "subtitle": "客户才能看到你在卖什么",
            "done": has_product,
            "route": "/client/products",
            "cta": "去发品" if not has_product else "完善产品",
            "hint": "产品少也可以先发 1 个，不求全。" if not has_product else "可以继续补规格和图片。",
        },
        {
            "id": "content",
            "order": 2,
            "title": "让别人找到你",
            "subtitle": "发内容 / 分发到多端",
            "done": has_content_action,
            "route": "/client/distribute",
            "cta": "去分发" if not has_content_action else "再发一条",
            "hint": "有内容才有人进站、来询盘。",
        },
        {
            "id": "inquiry",
            "order": 3,
            "title": "回复客户询盘",
            "subtitle": "有人问了就回，回了才可能成单",
            "done": weekly.get("followed", 0) > 0 and pending_all == 0,
            "route": "/client/inquiries",
            "cta": "去回复",
            "hint": f"本周收到 {weekly.get('received', 0)} 条，待回复 {pending_all} 条。不会写就让系统起一版。",
        },
    ]
    done_count = sum(1 for s in steps if s["done"])
    next_step = next((s for s in steps if not s["done"]), steps[-1])

    recent_inquiries = []
    try:
        rows = (
            db.query(Inquiry)
            .order_by(Inquiry.created_at.desc())
            .limit(8)
            .all()
        )
        for r in rows:
            recent_inquiries.append({
                "id": str(r.id),
                "buyer_name": r.name or "客户",
                "company": getattr(r, "company", "") or "",
                "email": r.email or "",
                "category": r.product or "产品",
                "status": r.status or "pending",
                "status_label": "新商机待响应" if (r.status in ("new", "pending", None, "")) else "跟进中",
                "time": r.created_at.isoformat() if r.created_at else "",
                "channel": r.source_channel or "website",
            })
    except Exception:
        pass

    # 真源：询盘数 / 在途订单数 / 成单结果（不写死最小值）
    inq_count = 0
    order_count = 0
    active_orders = 0
    try:
        inq_count = db.query(Inquiry).count()
        from app.models.order import Order
        from app.models.enums import OrderStatus
        order_count = db.query(Order).count()
        active_orders = (
            db.query(Order)
            .filter(Order.status.in_([
                OrderStatus.PENDING,
                OrderStatus.DEPOSIT_RECEIVED,
                OrderStatus.IN_PRODUCTION,
                OrderStatus.SHIPPED,
            ]))
            .count()
        )
    except Exception:
        pass

    win_loss: dict[str, Any] = {}
    recent_wins: list[dict[str, Any]] = []
    try:
        from app.services.acquisition import ops_card_store
        win_loss = ops_card_store.win_loss_stats(tenant_id=tid or "demo")
        if not win_loss.get("won_count"):
            win_loss = ops_card_store.win_loss_stats(tenant_id="")
        for w in (win_loss.get("won_items") or [])[:3]:
            recent_wins.append({
                "buyer": w.get("buyer_display") or w.get("inquiry_id") or "客户",
                "amount": w.get("amount") or 0,
                "currency": "USD",
                "note": w.get("note") or "",
            })
    except Exception:
        pass

    # 订单侧成单（持久）：已结清 = 成单金额来源
    won_amount = float(win_loss.get("won_amount") or 0) or 0.0
    won_count = int(win_loss.get("won_count") or 0)
    try:
        from app.models.order import Order
        from app.models.enums import OrderStatus
        from sqlalchemy import func
        row = db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
        ).filter(Order.status == OrderStatus.COMPLETED).first()
        if row:
            if not won_count:
                won_count = int(row[0] or 0)
            if not won_amount:
                won_amount = float(row[1] or 0)
            if won_count and not recent_wins:
                done_orders = (
                    db.query(Order)
                    .filter(Order.status == OrderStatus.COMPLETED)
                    .order_by(Order.updated_at.desc())
                    .limit(3)
                    .all()
                )
                for o in done_orders:
                    recent_wins.append({
                        "buyer": getattr(o, "customer_name", "") or o.order_number,
                        "amount": float(o.total_amount or 0),
                        "currency": o.currency or "USD",
                        "note": getattr(o, "product_summary", "") or "",
                    })
    except Exception:
        pass

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
        "recent_inquiries": recent_inquiries if recent_inquiries else None,
        "win_loss": {
            "won_count": won_count,
            "lost_count": int(win_loss.get("lost_count") or 0),
            "won_amount": won_amount,
            "plain_summary": win_loss.get("plain_summary") or "",
        },
        "recent_wins": recent_wins,
        "trade_stats": {
            "active_inquiries": inq_count,
            "pending_response": pending_all,
            "active_fulfillment_orders": active_orders,
            "total_orders": order_count,
            "won_count": won_count,
            "won_amount": won_amount,
        },
        "headline": (
            "今天该做的都做完了"
            if done_count >= 3
            else f"先做「{next_step['title']}」就行"
        ),
    }
