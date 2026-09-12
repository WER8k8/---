"""Token 账本 API"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.token_ledger import TokenLedgerEntry
from app.models.tenant import UserTenant
from app.models.user import User
from app.services.token_service import InsufficientTokenError, TokenService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/token", tags=["Token账本"])


def _resolve_tenant_for_user(db: Session, user: User) -> tuple[str | None, dict | None]:
    """租户用户 / 租户管理员解析 tenant_id；超管无绑定则返回 None。"""
    if user.role in ("admin", "super_admin"):
        link = (
            db.query(UserTenant)
            .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
            .first()
        )
        if link:
            return str(link.tenant_id), None
        return None, None
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .first()
    )
    if not link:
        return None, error_response(403, "未关联到任何租户")
    return str(link.tenant_id), None


class ConsumeRequest(BaseModel):
    tenant_id: str
    amount: int = Field(..., gt=0)
    reason: str = "ai_call"


class TopUpRequest(BaseModel):
    tenant_id: str
    amount: int = Field(..., gt=0)
    reason: str = "manual_topup"


@router.get("/balance/{tenant_id}")
def get_balance(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /balance/{tenant_id} 请求，获取相关资源。
    
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin", "tenant_admin"):
        return error_response(403, "权限不足")
    bal = TokenService(db).balance(tenant_id)
    return success_response(data={"tenant_id": tenant_id, "balance": bal})


@router.post("/consume")
def consume_tokens(
    req: ConsumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /consume 请求，consume相关资源。
    
    :param req: 请求对象
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin", "tenant_admin"):
        return error_response(403, "权限不足")
    try:
        bal = TokenService(db).consume(req.tenant_id, req.amount, req.reason)
    except InsufficientTokenError as e:
        return error_response(402, str(e))
    return success_response(data={"balance": bal}, message="扣减成功")


@router.post("/topup")
def topup_tokens(
    req: TopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管充值 Token（P1-09：充值后自动恢复暂停的租户）。"""
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可充值")
    svc = TokenService(db)
    bal = svc.credit(req.tenant_id, req.amount, req.reason)
    return success_response(
        data={"tenant_id": req.tenant_id, "balance": bal},
        message=f"已充值 {req.amount} Token，当前余额 {bal}",
    )


@router.get("/my-quota")
def get_my_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前登录租户 AI 流量余额与用量（客户侧公开透明）。"""
    tenant_id, err = _resolve_tenant_for_user(db, current_user)
    if err:
        return err
    if not tenant_id:
        return error_response(403, "无租户上下文")
    from app.models.tenant import Tenant
    from app.services.ai_traffic_provider_service import (
        get_tenant_ai_traffic_provider,
        provider_label,
    )
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    svc = TokenService(db)
    balance = svc.balance(tenant_id)
    quota_limit = svc._quota_limit(tenant)
    ai_quota_used = int(tenant.ai_quota_used or 0)
    pid = get_tenant_ai_traffic_provider(tenant)
    return success_response(
        data={
            "tenant_id": tenant_id,
            "balance": balance,
            "quota_limit": quota_limit,
            "quota_used": ai_quota_used,
            "ai_traffic_provider_label": provider_label(pid) if pid else None,
            "is_suspended": tenant.status == "suspended",
        }
    )


@router.get("/my-ledger")
def get_my_token_ledger(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前租户 Token 扣减/充值明细（公开透明）。"""
    tenant_id, err = _resolve_tenant_for_user(db, current_user)
    if err:
        return err
    if not tenant_id:
        return error_response(403, "无租户上下文")
    q = db.query(TokenLedgerEntry).filter(TokenLedgerEntry.tenant_id == tenant_id)
    total = q.count()
    rows = (
        q.order_by(TokenLedgerEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "items": [
                {
                    "id": r.id,
                    "delta": r.delta,
                    "amount": r.delta,
                    "balance_after": r.balance_after,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/quota-status/{tenant_id}")
def get_quota_status(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户配额状态（余额、是否停服、套餐上限）。"""
    if current_user.role not in ("admin", "super_admin", "tenant_admin"):
        return error_response(403, "权限不足")
    from app.models.tenant import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return error_response(404, "租户不存在")
    svc = TokenService(db)
    balance = svc.balance(tenant_id)
    quota_limit = svc._quota_limit(tenant)
    ai_quota_used = int(tenant.ai_quota_used or 0)
    from app.services.ai_traffic_provider_service import (
        get_tenant_ai_traffic_provider,
        provider_label,
    )
    pid = get_tenant_ai_traffic_provider(tenant)
    return success_response(
        data={
            "tenant_id": tenant_id,
            "status": tenant.status,
            "balance": balance,
            "quota_limit": quota_limit,
            "quota_used": ai_quota_used,
            "ai_quota_used": ai_quota_used,
            "is_suspended": tenant.status == "suspended",
            "is_suspended_by_token": tenant.status == "suspended",
            "plan_name": tenant.plan.name if tenant.plan else None,
            "suspension_pct": round(ai_quota_used / quota_limit * 100, 1) if quota_limit > 0 else 0,
            "ai_traffic_provider_id": pid,
            "ai_traffic_provider_label": provider_label(pid) if pid else None,
        }
    )


@router.get("/ledger")
def list_token_ledger(
    tenant_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /ledger 请求，列出相关资源。
    
    :param tenant_id: 租户ID
    :param page: 页码
    :param page_size: 每页条数
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin", "tenant_admin"):
        return error_response(403, "权限不足")
    q = db.query(TokenLedgerEntry).filter(TokenLedgerEntry.tenant_id == tenant_id)
    total = q.count()
    rows = (
        q.order_by(TokenLedgerEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "items": [
                {
                    "id": r.id,
                    "tenant_id": r.tenant_id,
                    "delta": r.delta,
                    "amount": r.delta,
                    "balance_after": r.balance_after,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": total,
        }
    )
