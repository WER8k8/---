"""静态 IP 槽位与浏览器指纹 API"""

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import (
    deny_unless_tenant_operator,
    is_platform_admin,
)
from app.db.session import get_db
from app.models.egress import BrowserProfile, EgressEndpoint
from app.models.tenant import Tenant, UserTenant
from app.models.user import User
from app.models.egress import EgressCostRecord, EgressPoolReplenishJob, EgressProvisionJob
from app.services.egress_jit_provision_service import (
    fulfill_manual_endpoint,
    process_pending_provision_jobs,
    retry_failed_slot,
    run_provision_job_background,
    serialize_provision_job,
)
from app.services.egress_quota_service import (
    platform_egress_overview,
    request_one_slot,
    tenant_egress_summary,
)


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/egress", tags=["静态IP与指纹"])


def _require_admin(user: User):
    """
    处理 _require_admin 相关业务逻辑。

    :param user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可操作")
    return None


class EgressCreate(BaseModel):
    region: str = Field(..., pattern="^(cn|global)$")
    host: str
    port: int = 0
    provider: Optional[str] = None
    label: Optional[str] = None
    tenant_id: Optional[str] = None


class ProfileCreate(BaseModel):
    name: str
    tenant_id: Optional[str] = None
    egress_endpoint_id: Optional[str] = None
    platform_account_id: Optional[str] = None
    fingerprint: dict = Field(default_factory=dict)


class AssignRequest(BaseModel):
    tenant_id: str


class FulfillEndpointRequest(BaseModel):
    host: str
    port: int = Field(..., ge=1, le=65535)
    proxy_username: str
    proxy_password: str
    label: Optional[str] = None
    upstream_ref: Optional[str] = None


@router.get("/overview")
def egress_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 egress_overview 相关业务逻辑。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    return success_response(data=platform_egress_overview(db))


@router.get("/tenants")
def egress_tenants(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 egress_tenants 相关业务逻辑。

    :param q: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    query = db.query(Tenant).filter(Tenant.is_active)
    if q:
        like = f"%{q}%"
        query = query.filter(Tenant.name.ilike(like) | Tenant.domain.ilike(like))
    rows = query.order_by(Tenant.created_at.desc()).limit(30).all()
    return success_response(
        data=[
            {
                "id": str(t.id),
                "name": t.name,
                "domain": t.domain,
                "status": t.status,
            }
            for t in rows
        ]
    )


@router.get("/endpoints")
def list_endpoints(
    region: Optional[str] = None,
    slot_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_endpoints）：处理相关业务逻辑并返回结果。

    :param region: 入参 (Optional[str])。
    :param slot_status: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    q = db.query(EgressEndpoint)
    if region:
        q = q.filter(EgressEndpoint.region == region)
    if slot_status:
        q = q.filter(EgressEndpoint.slot_status == slot_status)
    rows = q.order_by(EgressEndpoint.created_at.desc()).all()
    tenant_names: dict[str, str] = {}
    tids = {str(r.tenant_id) for r in rows if r.tenant_id}
    if tids:
        for t in db.query(Tenant.id, Tenant.name).filter(Tenant.id.in_(tids)).all():
            tenant_names[str(t[0])] = t[1] or str(t[0])[:8]
    return success_response(
        data=[
            {
                "id": r.id,
                "region": r.region,
                "host": r.host,
                "port": r.port,
                "provider": r.provider,
                "slot_status": r.slot_status,
                "tenant_id": r.tenant_id,
                "tenant_name": tenant_names.get(str(r.tenant_id)) if r.tenant_id else None,
                "label": r.label,
            }
            for r in rows
        ]
    )


@router.post("/endpoints")
def create_endpoint(
    req: EgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_endpoint）：处理相关业务逻辑并返回结果。

    :param req: 入参 (EgressCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    row = EgressEndpoint(
        region=req.region,
        host=req.host,
        port=req.port,
        provider=req.provider,
        label=req.label,
        tenant_id=req.tenant_id,
        slot_status="assigned" if req.tenant_id else "available",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(data={"id": row.id}, message="IP 槽位已创建")


@router.post("/endpoints/{endpoint_id}/assign")
def assign_endpoint(
    endpoint_id: str,
    req: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 assign_endpoint 相关业务逻辑。

    :param endpoint_id: 入参 (str)。
    :param req: 入参 (AssignRequest)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    row = db.query(EgressEndpoint).filter(EgressEndpoint.id == endpoint_id).first()
    if not row:
        return error_response(404, "IP 槽位不存在")
    tenant = db.query(Tenant).filter(Tenant.id == req.tenant_id, Tenant.is_active).first()
    if not tenant:
        return error_response(404, "租户不存在")
    row.tenant_id = req.tenant_id
    row.slot_status = "assigned"
    db.commit()
    return success_response(message="IP 槽位已分配")


@router.post("/endpoints/{endpoint_id}/release")
def release_endpoint(
    endpoint_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 release_endpoint 相关业务逻辑。

    :param endpoint_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    row = db.query(EgressEndpoint).filter(EgressEndpoint.id == endpoint_id).first()
    if not row:
        return error_response(404, "IP 槽位不存在")
    row.tenant_id = None
    row.slot_status = "disabled"
    db.commit()
    return success_response(message="IP 槽位已释放（不回到预库存池）")


@router.get("/profiles")
def list_profiles(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_profiles）：处理相关业务逻辑并返回结果。

    :param tenant_id: 入参 (Optional[str])。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    denied = deny_unless_tenant_operator(current_user)
    if denied:
        return denied
    q = db.query(BrowserProfile)
    if tenant_id:
        q = q.filter(BrowserProfile.tenant_id == tenant_id)
    rows = q.all()
    return success_response(
        data=[
            {
                "id": r.id,
                "name": r.name,
                "tenant_id": r.tenant_id,
                "egress_endpoint_id": r.egress_endpoint_id,
                "platform_account_id": r.platform_account_id,
            }
            for r in rows
        ]
    )


@router.post("/profiles")
def create_profile(
    req: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_profile）：处理相关业务逻辑并返回结果。

    :param req: 入参 (ProfileCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    denied = deny_unless_tenant_operator(current_user)
    if denied:
        return denied
    row = BrowserProfile(
        name=req.name,
        tenant_id=req.tenant_id,
        egress_endpoint_id=req.egress_endpoint_id,
        platform_account_id=req.platform_account_id,
        fingerprint=req.fingerprint,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(data={"id": row.id}, message="指纹环境已创建")


def _resolve_tenant_for_user(db: Session, user: User) -> Tenant | None:
    """
    处理 _resolve_tenant_for_user 相关业务逻辑。

    :param db: 入参 (Session)。
    :param user: 入参 (User)。

    :return: 返回 Tenant | None 类型的结果。
    """
    if is_platform_admin(user):
        return None
    link = (
        db.query(UserTenant)
        .filter(UserTenant.user_id == user.id, UserTenant.is_active.is_(True))
        .first()
    )
    if not link:
        return None
    return (
        db.query(Tenant)
        .filter(Tenant.id == link.tenant_id, Tenant.is_active.is_(True))
        .first()
    )


@router.get("/my")
def my_egress_slots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前租户已分配的 IP 槽位与配额。"""
    if is_platform_admin(current_user):
        return error_response(400, "超管请使用 /egress/endpoints")
    tenant = _resolve_tenant_for_user(db, current_user)
    if not tenant:
        return error_response(403, "未绑定租户")
    return success_response(data=tenant_egress_summary(db, tenant))


@router.post("/request-slot")
def request_egress_slot(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户申请 1 个 IP：按需向上游采购（约 1～3 分钟，无预库存）。"""
    if is_platform_admin(current_user):
        return error_response(400, "超管请使用分配接口")
    tenant = _resolve_tenant_for_user(db, current_user)
    if not tenant:
        return error_response(403, "未绑定租户")
    pair = request_one_slot(db, tenant)
    if not pair:
        return error_response(
            409,
            "已达套餐配额上限，或已有开通中的任务",
        )
    endpoint, job_id = pair
    if job_id:
        background_tasks.add_task(run_provision_job_background, job_id)
        from app.services.egress.provisioner import active_egress_provider
        prov = active_egress_provider()
        if prov == "asocks":
            msg = "已向 ASocks 提交开通，约 1～3 分钟"
        elif prov == "iproyal":
            msg = "IPRoyal 住宅ISP正在分配（从缓冲池），约 10 秒"
        else:
            msg = "演示环境：线路开通中"
    else:
        msg = "已提交申请，运营将在 1 个工作日内配置静态 IP"
    return success_response(
        data={
            "endpoint_id": endpoint.id,
            "job_id": job_id,
            "slot_status": endpoint.slot_status,
            "region": endpoint.region,
        },
        message=msg,
    )


@router.post("/endpoints/{endpoint_id}/fulfill")
def fulfill_endpoint(
    endpoint_id: str,
    req: FulfillEndpointRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管为待配置槽位录入真实代理（无第三方号池）。"""
    if err := _require_admin(current_user):
        return err
    try:
        row = fulfill_manual_endpoint(
            db,
            endpoint_id,
            host=req.host,
            port=req.port,
            proxy_username=req.proxy_username,
            proxy_password=req.proxy_password,
            label=req.label,
            upstream_ref=req.upstream_ref,
        )
    except ValueError as e:
        return error_response(400, str(e))
    if not row:
        return error_response(404, "IP 槽位不存在")
    return success_response(
        data={"id": row.id, "host": row.host, "port": row.port, "slot_status": row.slot_status},
        message="槽位已配置完成",
    )


@router.get("/provision-jobs/{job_id}")
def get_provision_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取（get_provision_job）：处理相关业务逻辑并返回结果。

    :param job_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    job = db.query(EgressProvisionJob).filter(EgressProvisionJob.id == job_id).first()
    if not job:
        return error_response(404, "任务不存在")
    if not is_platform_admin(current_user):
        tenant = _resolve_tenant_for_user(db, current_user)
        if not tenant or str(job.tenant_id) != str(tenant.id):
            return error_response(403, "无权查看该任务")
    return success_response(data=serialize_provision_job(job))


@router.post("/slots/{endpoint_id}/retry")
def retry_egress_slot(
    endpoint_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开通失败后重新向上游采购（仍不占预库存）。"""
    tenant = _resolve_tenant_for_user(db, current_user)
    if not tenant:
        return error_response(403, "未绑定租户")
    result = retry_failed_slot(db, tenant, endpoint_id)
    if not result.get("ok"):
        reason = result.get("reason", "retry_failed")
        if reason == "not_found":
            return error_response(404, "槽位不存在")
        return error_response(400, "仅失败槽位可重试开通")
    if result.get("job_id"):
        background_tasks.add_task(run_provision_job_background, result["job_id"])
    return success_response(
        data=result,
        message="已重新提交，请稍候刷新" if result.get("job_id") else "已恢复为待运营配置",
    )


@router.post("/ops/process-provisions")
def ops_process_egress_provisions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理排队中的按需采购任务（超管 / cron）。"""
    if err := _require_admin(current_user):
        return err
    data = process_pending_provision_jobs(db, limit=min(max(1, limit), 50))
    return success_response(data=data, message="已处理开通队列")


# ── 上游供应商 CRUD ─────────────────────────────────────────────


class SupplierCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    subtitle: Optional[str] = None
    adapter: str = Field(default="manual", pattern="^(manual|iproyal|asocks)$")
    ip_type: str = Field(default="static_residential")
    long_term_fixed: bool = True
    description: Optional[str] = None
    supports_pool_replenish: bool = False
    config: dict = Field(default_factory=dict)


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    subtitle: Optional[str] = None
    adapter: Optional[str] = Field(default=None, pattern="^(manual|iproyal|asocks)$")
    ip_type: Optional[str] = None
    long_term_fixed: Optional[bool] = None
    description: Optional[str] = None
    supports_pool_replenish: Optional[bool] = None
    config: Optional[dict] = None


@router.get("/suppliers")
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出（list_suppliers）：处理相关业务逻辑并返回结果。

    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    from app.services.egress_supplier_service import build_providers_page_payload
    return success_response(data=build_providers_page_payload(db))


@router.post("/suppliers")
def create_supplier(
    req: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建（create_supplier）：处理相关业务逻辑并返回结果。

    :param req: 入参 (SupplierCreate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    from app.services.egress_supplier_service import create_supplier as svc_create
    try:
        row = svc_create(
            db,
            code=req.code,
            name=req.name,
            adapter=req.adapter,
            subtitle=req.subtitle,
            ip_type=req.ip_type,
            long_term_fixed=req.long_term_fixed,
            description=req.description,
            supports_pool_replenish=req.supports_pool_replenish,
            config=req.config,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="供应商已添加")


@router.put("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: str,
    req: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新（update_supplier）：处理相关业务逻辑并返回结果。

    :param supplier_id: 入参 (str)。
    :param req: 入参 (SupplierUpdate)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    from app.services.egress_supplier_service import update_supplier as svc_update
    try:
        row = svc_update(
            db,
            supplier_id,
            name=req.name,
            subtitle=req.subtitle,
            adapter=req.adapter,
            ip_type=req.ip_type,
            long_term_fixed=req.long_term_fixed,
            description=req.description,
            supports_pool_replenish=req.supports_pool_replenish,
            config=req.config,
        )
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message="供应商已更新")


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除（delete_supplier）：处理相关业务逻辑并返回结果。

    :param supplier_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    from app.services.egress_supplier_service import delete_supplier as svc_delete
    try:
        svc_delete(db, supplier_id)
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(message="供应商已删除")


@router.post("/suppliers/{supplier_id}/activate")
def activate_supplier_route(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    处理 activate_supplier_route 相关业务逻辑。

    :param supplier_id: 入参 (str)。
    :param db: 入参 (Session)。
    :param current_user: 入参 (User)。

    :return: 返回处理结果（或 None）。
    """
    if err := _require_admin(current_user):
        return err
    from app.services.egress_supplier_service import activate_supplier as svc_activate
    try:
        row = svc_activate(db, supplier_id)
    except ValueError as exc:
        return error_response(400, str(exc))
    return success_response(data=row, message=f"已切换为 {row.get('name')}")


@router.get("/costs")
def list_costs(
    page: int = 1,
    per_page: int = 50,
    operation: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询 IPRoyal 成本/续费记录。"""
    if err := _require_admin(current_user):
        return err
    q = db.query(EgressCostRecord)
    if operation:
        q = q.filter(EgressCostRecord.operation == operation)
    total = q.count()
    rows = (
        q.order_by(EgressCostRecord.created_at.desc())
        .offset((max(1, page) - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return success_response(data={
        "total": total,
        "page": page,
        "items": [
            {
                "id": r.id,
                "endpoint_id": r.endpoint_id,
                "provider": r.provider,
                "operation": r.operation,
                "iproyal_order_id": r.iproyal_order_id,
                "quantity": r.quantity,
                "unit_price_cents": r.unit_price_cents,
                "total_price_cents": r.total_price_cents,
                "currency": r.currency,
                "plan_days": r.plan_days,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    })


@router.get("/costs/summary")
def costs_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """成本统计汇总。"""
    if err := _require_admin(current_user):
        return err
    purchases = (
        db.query(EgressCostRecord)
        .filter(EgressCostRecord.operation == "purchase")
        .count()
    )
    renewals = (
        db.query(EgressCostRecord)
        .filter(EgressCostRecord.operation == "renew")
        .count()
    )
    renew_failures = (
        db.query(EgressCostRecord)
        .filter(EgressCostRecord.operation == "renew_failed")
        .count()
    )
    total_cost = 0
    for r in db.query(EgressCostRecord).all():
        total_cost += (r.total_price_cents or 0)
    active_ips = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.slot_status == "assigned",
        )
        .count()
    )
    pool_available = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.slot_status == "available",
        )
        .count()
    )
    return success_response(data={
        "purchase_count": purchases,
        "renewal_count": renewals,
        "renew_failure_count": renew_failures,
        "total_cost_usd": round(total_cost / 100, 2),
        "total_cost_cents": total_cost,
        "active_ips": active_ips,
        "pool_available": pool_available,
    })


@router.get("/pool/status")
def pool_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """IPRoyal 缓冲池状态。"""
    if err := _require_admin(current_user):
        return err
    from app.core.config import settings as cfg
    available = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.slot_status == "available",
        )
        .count()
    )
    assigned = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.slot_status == "assigned",
        )
        .count()
    )
    expiring_soon = (
        db.query(EgressEndpoint)
        .filter(
            EgressEndpoint.provider == "iproyal",
            EgressEndpoint.slot_status == "assigned",
            EgressEndpoint.expire_date.isnot(None),
        )
        .count()
    )
    return success_response(data={
        "pool_available": available,
        "assigned": assigned,
        "expiring_soon": expiring_soon,
        "low_watermark": cfg.IPROYAL_POOL_LOW_WATERMARK,
        "batch_size": cfg.IPROYAL_BATCH_SIZE,
    })


@router.post("/pool/replenish")
def manual_replenish(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发缓冲池补充。"""
    if err := _require_admin(current_user):
        return err
    from app.services.egress_replenish_service import check_and_replenish_pool
    result = check_and_replenish_pool(db)
    return success_response(data=result, message="补充检查完成")


# ── 定时任务端点（OPS_CRON_TOKEN 保护）──────────────────────


def _require_cron(request):
    """校验 OPS_CRON_TOKEN。"""
    from app.core.config import settings as cfg
    token = (cfg.OPS_CRON_TOKEN or "").strip()
    if not token:
        return None  # 未配置则不校验
    auth = request.headers.get("authorization", "")
    if auth == f"Bearer {token}" or auth == token:
        return None
    return error_response(403, "无效的 cron token")


@router.post("/ops/check-pool")
def ops_check_pool(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """定时任务：检查缓冲池水位，不足自动补充。"""
    if err := _require_admin(current_user):
        return err
    from app.services.egress_replenish_service import check_and_replenish_pool
    result = check_and_replenish_pool(db)
    # 补充后尝试分配排队任务
    if result.get("replenish_triggered"):
        from app.services.egress_replenish_service import fulfill_pending_jobs_from_pool
        fulfill_pending_jobs_from_pool(db)
    return success_response(data=result, message="池水位检查完成")


@router.post("/ops/check-renewals")
def ops_check_renewals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """定时任务：检查到期前7天的IP并自动续费（养号核心）。"""
    if err := _require_admin(current_user):
        return err
    from app.services.egress_replenish_service import auto_renew_expiring_ips
    result = auto_renew_expiring_ips(db)
    return success_response(data=result, message="续费检查完成")


@router.post("/ops/cleanup-expired")
def ops_cleanup_expired(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """定时任务：清理续费失败且过期的IP。"""
    if err := _require_admin(current_user):
        return err
    from app.services.egress_replenish_service import cleanup_expired_ips
    result = cleanup_expired_ips(db)
    return success_response(data=result, message="过期IP清理完成")
