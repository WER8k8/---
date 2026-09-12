"""客户裂变推荐系统路由"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.referral_service import ReferralService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/referral", tags=["呼朋唤友推荐"])


@router.get("/my-code")
def get_my_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的邀请码和链接"""
    from app.models.tenant import UserTenant
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id, UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您不属于任何租户")

    svc = ReferralService(db)
    code = svc.generate_code(link.tenant_id)
    return success_response(data={
        "code": code.code,
        "invite_link": f"https://saas.youding.com/tenants/register?ref={code.code}",
        "total_referred": code.total_referred,
    })


@router.post("/generate")
def generate_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成/刷新邀请码"""
    from app.models.tenant import UserTenant
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id, UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您不属于任何租户")

    svc = ReferralService(db)
    code = svc.generate_code(link.tenant_id)
    return success_response(data={"code": code.code})


@router.get("/stats")
def get_referral_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取邀请统计"""
    from app.models.tenant import UserTenant
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id, UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您不属于任何租户")

    svc = ReferralService(db)
    return success_response(data=svc.get_referral_stats(link.tenant_id))


@router.get("/records")
def get_referral_records(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取邀请记录"""
    from app.models.tenant import UserTenant
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id, UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您不属于任何租户")

    svc = ReferralService(db)
    items, total = svc.get_my_records(link.tenant_id, page, page_size)
    return success_response(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/apply/{code}")
def apply_referral(
    code: str,
    db: Session = Depends(get_db),
):
    """应用邀请码（公开接口，注册时调用）"""
    # 新注册用户还没有tenant_id，所以通过request body传入
    # 这里只做验证，实际绑定在注册流程中完成
    from app.models.tenant import Tenant
    # 验证码是否存在
    from app.models.referral import ReferralCode
    ref = db.query(ReferralCode).filter(
        ReferralCode.code == code,
        ReferralCode.is_active,
    ).first()
    if not ref:
        return success_response(data={"valid": False, "message": "邀请码无效"})
    tenant = db.query(Tenant).filter(Tenant.id == ref.tenant_id).first()
    name = tenant.name if tenant else "未知"
    return success_response(data={"valid": True, "inviter": name, "message": "邀请码有效"})


@router.post("/sync-rewards")
def sync_referral_rewards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """P1-06：发放待处理裂变奖励（现金券/Token/套餐券等）。"""
    from app.models.tenant import UserTenant
    from app.services.referral_reward_service import process_pending_rewards
    link = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id, UserTenant.is_active,
    ).first()
    if not link:
        return error_response(403, "您不属于任何租户")
    granted = process_pending_rewards(db, link.tenant_id)
    return success_response(
        data={"granted": granted, "count": len(granted)},
        message=f"已处理 {len(granted)} 条奖励",
    )


@router.get("/reward-types")
def list_reward_types():
    """P1-06：支持的奖励类型说明。"""
    from app.services.referral_reward_service import TIER_REWARDS
    return success_response(
        data=[
            {
                "invites": t,
                "reward_type": r,
                "label": label,
                "amount": amount,
            }
            for t, r, label, amount in TIER_REWARDS
        ]
    )


@router.get("/leaderboard")
def get_leaderboard(
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
):
    """邀请排行榜（公开接口）"""
    svc = ReferralService(db)
    return success_response(data={"items": svc.get_leaderboard(limit)})


@router.get("/admin/cash-coupons/pending")
def list_pending_cash_coupons_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：待线下核销的现金券列表。"""
    from app.services.referral_redeem_service import list_pending_cash_coupons
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可查看")
    items = list_pending_cash_coupons(db)
    return success_response(data={"items": items, "count": len(items)})


@router.post("/admin/cash-coupons/{record_id}/redeem")
def redeem_cash_coupon_admin(
    record_id: str,
    note: str = Query("", max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管：确认现金券已线下兑付。"""
    from app.services.referral_redeem_service import redeem_cash_coupon
    ok, msg, data = redeem_cash_coupon(
        db, record_id=record_id, admin_user=current_user, note=note
    )
    if not ok:
        return error_response(400, msg)
    return success_response(data=data, message=msg)
