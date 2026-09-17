# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""License Management API - 许可证管理接口（P1-5 扩展：设备指纹 + 授权码 + 套餐订单）"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.models.license import License, DeviceFingerprint, LicenseCode, LicenseOrder
from app.models.tenant import Tenant, TenantPlan
from app.models.user import User
from app.services import license_service

ROUTE_PREFIX = ""
router = APIRouter(prefix="/license", tags=["license"])


def _generate_license_key() -> str:
    """生成许可证密钥（格式：XXXX-XXXX-XXXX-XXXX）"""
    raw = uuid.uuid4().hex.upper()
    return "-".join([raw[i:i+4] for i in range(0, 32, 4)])


def _generate_multi_license_keys(count: int) -> list[str]:
    """批量生成许可证密钥"""
    keys = []
    while len(keys) < count:
        key = _generate_license_key()
        if key not in keys:
            keys.append(key)
    return keys


@router.post("/generate")
def generate_licenses(
    count: int = Query(1, ge=1, le=100),
    plan_code: str = Query("pro"),
    duration_days: int = Query(365),
    max_devices: int = Query(1),
    ai_quota: int = Query(10000),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """批量生成许可证"""
    plan = db.query(TenantPlan).filter(TenantPlan.code == plan_code).first()
    if not plan:
        plan = db.query(TenantPlan).filter(TenantPlan.code == "pro").first()
        if not plan:
            raise HTTPException(status_code=404, detail="套餐不存在")

    keys = _generate_multi_license_keys(count)
    licenses = []
    now = datetime.now(timezone.utc)
    for key in keys:
        license_obj = License(
            license_key=key,
            plan_code=plan_code,
            status="inactive",
            expires_at=now + timedelta(days=duration_days),
            max_devices=max_devices,
            ai_quota=ai_quota,
            created_by=str(admin.id),
        )
        db.add(license_obj)
        licenses.append(license_obj)

    db.commit()
    return success_response(
        data={
            "count": len(licenses),
            "plan_code": plan_code,
            "duration_days": duration_days,
            "licenses": [
                {
                    "id": str(l.id),
                    "license_key": l.license_key,
                    "status": l.status,
                    "expires_at": l.expires_at.isoformat() if l.expires_at else None,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in licenses
            ],
        },
        message=f"成功生成 {count} 个许可证",
    )


@router.post("/activate")
def activate_license(
    license_key: str,
    hardware_id: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """激活许可证"""
    license_obj = db.query(License).filter(License.license_key == license_key.strip()).first()
    if not license_obj:
        return error_response(404, "许可证不存在")

    if license_obj.status == "active":
        if license_obj.hardware_id and hardware_id and license_obj.hardware_id != hardware_id:
            return error_response(403, "该许可证已在其他设备激活")
        return success_response(
            data={
                "id": str(license_obj.id),
                "license_key": license_obj.license_key,
                "status": license_obj.status,
                "plan_code": license_obj.plan_code,
                "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            },
            message="许可证已激活",
        )

    if license_obj.status == "expired":
        return error_response(403, "许可证已过期")

    if license_obj.status == "revoked":
        return error_response(403, "许可证已被吊销")

    tenant = db.query(Tenant).filter(Tenant.id == current_user.id).first()
    if not tenant:
        plan_query = db.query(TenantPlan).filter(TenantPlan.code == license_obj.plan_code).first()
        plan_id = str(plan_query.id) if plan_query else str(db.query(TenantPlan).first().id)
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=f"{current_user.display_name} 的租户",
            domain=f"{current_user.username}.dev.local",
            plan_id=plan_id,
            status="active",
            expires_at=license_obj.expires_at,
        )
        db.add(tenant)
        db.flush()

    license_obj.status = "active"
    license_obj.activated_at = datetime.now(timezone.utc)
    license_obj.hardware_id = hardware_id.strip() if hardware_id else None
    license_obj.tenant_id = str(tenant.id)
    db.commit()
    db.refresh(license_obj)
    return success_response(
        data={
            "id": str(license_obj.id),
            "license_key": license_obj.license_key,
            "status": license_obj.status,
            "plan_code": license_obj.plan_code,
            "tenant_id": str(license_obj.tenant_id),
            "activated_at": license_obj.activated_at.isoformat() if license_obj.activated_at else None,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
        },
        message="许可证激活成功",
    )


@router.post("/{license_id}/revoke")
def revoke_license(
    license_id: str,
    reason: str = "",
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """吊销许可证"""
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        return error_response(404, "许可证不存在")

    if license_obj.status == "revoked":
        return error_response(400, "许可证已被吊销")

    license_obj.status = "revoked"
    license_obj.notes = (license_obj.notes or "") + f"\n[吊销] {reason}" if reason else ""
    db.commit()
    return success_response(message="许可证已吊销")


@router.get("/")
def list_licenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    plan_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取许可证列表"""
    query = db.query(License).order_by(License.created_at.desc())
    if status:
        query = query.filter(License.status == status)
    if plan_code:
        query = query.filter(License.plan_code == plan_code)

    total = query.count()
    licenses = query.offset((page - 1) * page_size).limit(page_size).all()
    return success_response(
        data=[
            {
                "id": str(l.id),
                "license_key": l.license_key,
                "plan_code": l.plan_code,
                "status": l.status,
                "tenant_id": str(l.tenant_id) if l.tenant_id else None,
                "activated_at": l.activated_at.isoformat() if l.activated_at else None,
                "expires_at": l.expires_at.isoformat() if l.expires_at else None,
                "hardware_id": l.hardware_id,
                "max_devices": l.max_devices,
                "ai_quota": l.ai_quota,
                "notes": l.notes,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in licenses
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{license_id}")
def get_license(
    license_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """获取许可证详情"""
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        return error_response(404, "许可证不存在")

    tenant_info = None
    if license_obj.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == license_obj.tenant_id).first()
        if tenant:
            tenant_info = {
                "id": str(tenant.id),
                "name": tenant.name,
                "domain": tenant.domain,
                "status": tenant.status,
            }

    return success_response(
        data={
            "id": str(license_obj.id),
            "license_key": license_obj.license_key,
            "plan_code": license_obj.plan_code,
            "status": license_obj.status,
            "tenant": tenant_info,
            "activated_at": license_obj.activated_at.isoformat() if license_obj.activated_at else None,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            "hardware_id": license_obj.hardware_id,
            "max_devices": license_obj.max_devices,
            "ai_quota": license_obj.ai_quota,
            "notes": license_obj.notes,
            "created_by": str(license_obj.created_by) if license_obj.created_by else None,
            "created_at": license_obj.created_at.isoformat() if license_obj.created_at else None,
            "updated_at": license_obj.updated_at.isoformat() if license_obj.updated_at else None,
        }
    )


@router.put("/{license_id}")
def update_license(
    license_id: str,
    plan_code: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    max_devices: Optional[int] = None,
    ai_quota: Optional[int] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """更新许可证"""
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        return error_response(404, "许可证不存在")

    if plan_code:
        license_obj.plan_code = plan_code
    if expires_at:
        license_obj.expires_at = expires_at.replace(tzinfo=timezone.utc)
    if max_devices is not None:
        license_obj.max_devices = max_devices
    if ai_quota is not None:
        license_obj.ai_quota = ai_quota
    if notes is not None:
        license_obj.notes = notes

    db.commit()
    db.refresh(license_obj)
    return success_response(
        data={
            "id": str(license_obj.id),
            "license_key": license_obj.license_key,
            "plan_code": license_obj.plan_code,
            "status": license_obj.status,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            "max_devices": license_obj.max_devices,
            "ai_quota": license_obj.ai_quota,
            "notes": license_obj.notes,
        },
        message="许可证更新成功",
    )


@router.delete("/{license_id}")
def delete_license(
    license_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """删除许可证"""
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        return error_response(404, "许可证不存在")

    if license_obj.status == "active":
        return error_response(400, "不能删除已激活的许可证，请先吊销")

    db.delete(license_obj)
    db.commit()
    return success_response(message="许可证已删除")


@router.get("/status")
def get_license_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的许可证状态"""
    license_obj = (
        db.query(License)
        .filter(License.tenant_id == str(current_user.id), License.status == "active")
        .first()
    )
    if not license_obj:
        return success_response(
            data={
                "has_license": False,
                "status": "none",
                "message": "未激活许可证",
            }
        )

    now = datetime.now(timezone.utc)
    is_expired = license_obj.expires_at and license_obj.expires_at < now
    days_remaining = (license_obj.expires_at - now).days if license_obj.expires_at else 0
    return success_response(
        data={
            "has_license": True,
            "status": "expired" if is_expired else "active",
            "license_key": license_obj.license_key,
            "plan_code": license_obj.plan_code,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            "days_remaining": days_remaining,
            "ai_quota": license_obj.ai_quota,
            "activated_at": license_obj.activated_at.isoformat() if license_obj.activated_at else None,
        }
    )


# ═══════════════════════════════════════════════════════
#  P1-5 新增路由：设备指纹 + 授权码激活 + 套餐订单
# ═══════════════════════════════════════════════════════

@router.post("/v2/activate")
def v2_activate(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """激活授权码（TL1.xxxxx.xxxxx 格式），绑定设备指纹。"""
    code = req.get("code", "").strip()
    fingerprint_hash = req.get("fingerprint_hash", "").strip()
    device_info = req.get("device_info", {})
    if not code:
        return error_response(400, "授权码不能为空")

    try:
        lic = license_service.activate_code(
            db, code, str(current_user.id), fingerprint_hash
        )
        db.commit()
        return success_response(
            data={
                "code": lic.code,
                "plan_type": lic.plan_type,
                "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
                "status": lic.status,
            },
            message="授权激活成功",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.get("/v2/status")
def v2_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询当前用户授权状态（TL1 授权码体系）。"""
    status = license_service.check_license_status(db, str(current_user.id))
    return success_response(data=status)


@router.post("/v2/orders")
def v2_create_order(
    req: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建授权套餐订单。"""
    plan_type = req.get("plan_type", "")
    if plan_type not in ("half_year", "yearly"):
        return error_response(400, "套餐类型无效")

    order = license_service.create_order(
        db,
        user_id=str(current_user.id),
        plan_type=plan_type,
        payment_method=req.get("payment_method"),
        payment_ref=req.get("payment_ref"),
    )
    db.commit()
    return success_response(
        data={
            "order_id": str(order.id),
            "plan_type": order.plan_type,
            "amount_cents": order.amount_cents,
        },
        message="订单已提交，等待管理员确认",
    )


@router.get("/v2/orders")
def v2_list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询当前用户订单列表（分页）。"""
    query = (
        db.query(LicenseOrder)
        .filter(LicenseOrder.user_id == current_user.id)
        .order_by(LicenseOrder.created_at.desc())
    )
    total = query.count()
    orders = query.offset((page - 1) * page_size).limit(page_size).all()
    return success_response(data={
        "items": [
            {
                "id": str(o.id),
                "plan_type": o.plan_type,
                "amount_cents": o.amount_cents,
                "payment_method": o.payment_method,
                "status": o.status,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ]
    })


@router.post("/v2/orders/{order_id}/confirm")
def v2_confirm_order(
    order_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """管理员确认订单 → 生成 TL1 授权码。"""
    try:
        lic = license_service.confirm_order(db, order_id, str(admin.id))
        db.commit()
        return success_response(
            data={"code": lic.code, "plan_type": lic.plan_type},
            message="订单已确认，授权码已生成",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.get("/v2/admin/codes")
def v2_list_codes(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """管理员查看所有 TL1 授权码。"""
    codes = db.query(LicenseCode).order_by(LicenseCode.created_at.desc()).limit(200).all()
    return success_response(data={
        "items": [
            {
                "id": str(c.id),
                "code": c.code,
                "plan_type": c.plan_type,
                "user_id": str(c.user_id) if c.user_id else None,
                "status": c.status,
                "activated_at": c.activated_at.isoformat() if c.activated_at else None,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            }
            for c in codes
        ]
    })
