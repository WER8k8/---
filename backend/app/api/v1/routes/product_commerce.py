# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""产品商业化 API — FIX-32/33/34

端点：
- GET  /plans          - 套餐列表
- GET  /value-proposition - 价值主张
- GET  /credits/system - 积分体系
- GET  /credits/balance - 用户积分余额
- POST /credits/purchase - 购买积分包
"""

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.core.response import success_response, error_response
from app.core.cache import async_cache_decorator
from app.core.product_commerce import (
    get_plans_for_display,
    get_value_proposition,
    get_credit_system,
    CREDIT_COST,
    REFERRAL_BONUS,
)

router = APIRouter(tags=["产品商业化"])


# ============================================================
# 套餐
# ============================================================

@router.get("/plans")
@async_cache_decorator(ttl=3600)
async def list_plans():
    """获取所有套餐（公开接口，缓存1小时）。"""
    return success_response(data={"plans": get_plans_for_display()})


# ============================================================
# 价值主张
# ============================================================

@router.get("/value-proposition")
@async_cache_decorator(ttl=86400)
async def value_proposition():
    """获取产品价值主张（公开接口，缓存24小时）。"""
    return success_response(data=get_value_proposition())


# ============================================================
# 积分体系
# ============================================================

@router.get("/credits/system")
@async_cache_decorator(ttl=3600)
async def credit_system_info():
    """获取积分体系信息（公开接口）。"""
    return success_response(data=get_credit_system())


@router.get("/credits/balance")
async def get_credit_balance(current_user=Depends(get_current_user)):
    """获取当前用户的积分余额。"""
    try:
        from app.db.session import SessionLocal
        from app.models.prospect_lead import ProspectLead
        import datetime
        # 简化实现：从数据库统计
        db = SessionLocal()
        try:
            now = datetime.datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 本月已使用的积分（从线索数量和邮件数量估算）
            leads_this_month = (
                db.query(ProspectLead)
                .filter(ProspectLead.created_at >= month_start)
                .count()
            )
            # 返回模拟余额（后续接入真实积分表）
            return success_response(data={
                "user_id": current_user.id,
                "balance": {
                    "monthly": 200,          # 月度免费积分
                    "purchased": 0,           # 已购买积分
                    "bonus": 0,               # 奖励积分
                    "rollover": 0,            # 结转积分
                    "total": 200,
                },
                "usage_this_month": {
                    "leads_searched": leads_this_month,
                    "credits_spent": leads_this_month * 1.0,
                },
                "credit_costs": {a.value: cost for a, cost in CREDIT_COST.items()},
            })
        finally:
            db.close()
    except Exception as e:
        return error_response(message=f"查询积分失败: {str(e)}", code=500)


@router.post("/credits/purchase")
async def purchase_credits(
    pack_id: str = Query(..., description="积分包ID"),
    current_user=Depends(get_current_user),
):
    """购买积分包（模拟接口，后续接入真实支付）。"""
    from app.core.product_commerce import CREDIT_PACKS
    pack = next((p for p in CREDIT_PACKS if p.id == pack_id), None)
    if not pack:
        return error_response(message="积分包不存在", code=404)

    # 模拟购买成功
    return success_response(data={
        "order_id": f"credit-{pack_id}-{current_user.id}",
        "pack": {
            "id": pack.id,
            "name": pack.name,
            "credits": pack.credits,
            "price": pack.price_usd,
        },
        "status": "completed",
        "message": f"成功购买 {pack.credits} 积分",
    })


# ============================================================
# 推荐奖励
# ============================================================

@router.get("/referral/info")
@async_cache_decorator(ttl=3600)
async def referral_info(current_user=Depends(get_current_user)):
    """获取推荐奖励信息。"""
    return success_response(data={
        "referral_code": f"REF-{current_user.id[:8].upper()}",
        "bonus": REFERRAL_BONUS,
        "total_earned": 0,  # 后续接入真实数据
        "referral_link": f"https://uj-china.com/ref/{current_user.id[:8]}",
    })