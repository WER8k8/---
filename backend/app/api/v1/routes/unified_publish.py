"""统一发布台 API — 汇聚母版、任务、状态的一站式入口

工作流: ContentMaster(母版) → PublishTask(任务队列) → 执行结果
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.content import Platform, PlatformAccount, PublishLog, PublishTask
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant, UserTenant
from app.models.user import User


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/unified-publish", tags=["统一发布台"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_tenant_access(user: User, tenant_id: str, db: Session) -> bool:
    """执行 has_tenant_access 相关逻辑处理。
    
    :param user: 用户对象
    :param tenant_id: 租户ID
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    if user.role in ("admin", "super_admin"):
        return True
    return (
        db.query(UserTenant)
        .filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant_id,
            UserTenant.is_active,
        )
        .first()
    ) is not None


def _serialize_task(t: PublishTask) -> dict[str, Any]:
    """执行 serialize_task 相关逻辑处理。
    
    :param t: 参数 t
    :return: 返回处理结果。
    """
    return {
        "id": t.id,
        "content_master_id": t.content_master_id,
        "platform_id": t.platform_id,
        "account_id": t.account_id,
        "region": t.region,
        "status": t.status,
        "publish_type": t.publish_type,
        "primary_url": t.primary_url,
        "secondary_url": t.secondary_url,
        "published_url": t.published_url,
        "error_message": t.error_message,
        "retry_count": t.retry_count,
        "scheduled_time": t.scheduled_time.isoformat() if t.scheduled_time else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "published_at": t.published_at.isoformat() if t.published_at else None,
    }


# ---------------------------------------------------------------------------
# 1. 发布概览仪表板
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def get_publish_dashboard(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取发布任务统计概览（按状态分组）。"""
    q = db.query(PublishTask)
    if tenant_id:
        if not _has_tenant_access(current_user, tenant_id, db):
            return error_response(403, "无权访问该租户")
        # 关联 content_master 过滤
        master_ids = [
            m.id
            for m in db.query(ContentMaster.id)
            .filter(ContentMaster.tenant_id == tenant_id)
            .all()
        ]
        q = q.filter(PublishTask.content_master_id.in_(master_ids))
    elif current_user.role not in ("admin", "super_admin"):
        tenant_ids = [
            ut.tenant_id
            for ut in db.query(UserTenant)
            .filter(UserTenant.user_id == current_user.id, UserTenant.is_active)
            .all()
        ]
        master_ids = [
            m.id
            for m in db.query(ContentMaster.id)
            .filter(ContentMaster.tenant_id.in_(tenant_ids))
            .all()
        ]
        q = q.filter(PublishTask.content_master_id.in_(master_ids))

    total = q.count()
    pending = q.filter(PublishTask.status == "pending").count()
    processing = q.filter(PublishTask.status == "processing").count()
    success = q.filter(PublishTask.status == "success").count()
    failed = q.filter(PublishTask.status == "failed").count()
    return success_response(
        data={
            "total": total,
            "pending": pending,
            "processing": processing,
            "success": success,
            "failed": failed,
            "success_rate": round(success / total * 100, 1) if total > 0 else 0,
        }
    )


# ---------------------------------------------------------------------------
# 2. 发布任务列表（跨母版）
# ---------------------------------------------------------------------------

@router.get("/tasks")
def list_publish_tasks(
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取发布任务列表，支持按租户/状态/区域过滤。"""
    q = db.query(PublishTask)
    if tenant_id:
        if not _has_tenant_access(current_user, tenant_id, db):
            return error_response(403, "无权访问该租户")
        master_ids = [
            m.id
            for m in db.query(ContentMaster.id)
            .filter(ContentMaster.tenant_id == tenant_id)
            .all()
        ]
        q = q.filter(PublishTask.content_master_id.in_(master_ids))
    elif current_user.role not in ("admin", "super_admin"):
        tenant_ids = [
            ut.tenant_id
            for ut in db.query(UserTenant)
            .filter(UserTenant.user_id == current_user.id, UserTenant.is_active)
            .all()
        ]
        master_ids = [
            m.id
            for m in db.query(ContentMaster.id)
            .filter(ContentMaster.tenant_id.in_(tenant_ids))
            .all()
        ]
        q = q.filter(PublishTask.content_master_id.in_(master_ids))

    if status:
        q = q.filter(PublishTask.status == status)
    if region:
        q = q.filter(PublishTask.region == region)

    total = q.count()
    items = (
        q.order_by(PublishTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "items": [_serialize_task(t) for t in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


# ---------------------------------------------------------------------------
# 3. 批量重试失败任务
# ---------------------------------------------------------------------------

class BatchRetryRequest(BaseModel):
    task_ids: list[str]


@router.post("/tasks/batch-retry")
def batch_retry_tasks(
    req: BatchRetryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量重试失败的发布任务。"""
    if not req.task_ids:
        return error_response(400, "task_ids 不能为空")

    tasks = (
        db.query(PublishTask)
        .filter(
            PublishTask.id.in_(req.task_ids),
            PublishTask.status == "failed",
        )
        .all()
    )
    if not tasks:
        return error_response(404, "未找到可重试的失败任务")

    retried: list[str] = []
    skipped: list[str] = []
    for task in tasks:
        if task.retry_count >= task.max_retries:
            skipped.append(task.id)
            continue
        task.status = "pending"
        task.error_message = None
        task.retry_count += 1
        retried.append(task.id)

    db.commit()
    return success_response(
        data={"retried": retried, "skipped_max_retries": skipped},
        message=f"已重置 {len(retried)} 条任务为待发布",
    )


# ---------------------------------------------------------------------------
# 4. 取消/删除待发布任务
# ---------------------------------------------------------------------------

class BatchCancelRequest(BaseModel):
    task_ids: list[str]


@router.post("/tasks/batch-cancel")
def batch_cancel_tasks(
    req: BatchCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量取消 pending 状态的发布任务。"""
    if not req.task_ids:
        return error_response(400, "task_ids 不能为空")

    tasks = (
        db.query(PublishTask)
        .filter(
            PublishTask.id.in_(req.task_ids),
            PublishTask.status == "pending",
        )
        .all()
    )
    cancelled_ids = [t.id for t in tasks]
    for t in tasks:
        db.delete(t)
    db.commit()
    return success_response(
        data={"cancelled": cancelled_ids, "count": len(cancelled_ids)},
        message=f"已取消 {len(cancelled_ids)} 条任务",
    )


# ---------------------------------------------------------------------------
# 5. 单个任务详情 + 日志
# ---------------------------------------------------------------------------

@router.get("/tasks/{task_id}")
def get_publish_task_detail(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个发布任务详情及日志。"""
    task = db.query(PublishTask).filter(PublishTask.id == task_id).first()
    if not task:
        return error_response(404, "任务不存在")

    logs = (
        db.query(PublishLog)
        .filter(PublishLog.task_id == task_id)
        .order_by(PublishLog.id.asc())
        .all()
    )
    log_items = [
        {"level": l.level, "message": l.message}
        for l in logs
    ]
    return success_response(
        data={
            **_serialize_task(task),
            "logs": log_items,
        }
    )


# ---------------------------------------------------------------------------
# 6. 从母版一键发布（入口聚合，转发到 content_master 路由）
# ---------------------------------------------------------------------------

class QuickPublishRequest(BaseModel):
    master_id: str
    platform_ids: list[str]
    account_ids: Optional[list[str]] = None


@router.post("/quick-publish")
def quick_publish(
    req: QuickPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一键发布：直接从母版 ID + 平台 IDs 创建发布任务。
    
    等效于 POST /content-masters/{master_id}/publish，
    提供更友好的统一入口。
    """
    from app.services.hub_urls import build_dual_links
    from sqlalchemy.orm import selectinload
    master = (
        db.query(ContentMaster)
        .options(selectinload(ContentMaster.platforms))
        .filter(ContentMaster.id == req.master_id)
        .first()
    )
    if not master:
        return error_response(404, "母版不存在")
    if not _has_tenant_access(current_user, master.tenant_id, db):
        return error_response(403, "无权操作该租户")

    # 复用已加载的 tenant_id，减少重复查询
    tenant = db.query(Tenant).filter(Tenant.id == master.tenant_id).first()
    if not tenant:
        return error_response(400, "租户不存在")

    platforms = (
        db.query(Platform)
        .filter(Platform.id.in_(req.platform_ids), Platform.is_active)
        .all()
    )
    if not platforms:
        return error_response(400, "未找到有效平台")

    task_ids: list[str] = []
    for plat in platforms:
        account = None
        if req.account_ids:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.id.in_(req.account_ids),
                    PlatformAccount.platform_id == plat.id,
                    PlatformAccount.is_active,
                )
                .first()
            )
        if not account:
            account = (
                db.query(PlatformAccount)
                .filter(
                    PlatformAccount.platform_id == plat.id,
                    PlatformAccount.is_active,
                )
                .first()
            )
        if not account:
            continue

        plat_code = (plat.name or "platform")[:32].replace(" ", "_")
        primary_url, secondary_url = build_dual_links(tenant, master, plat_code)
        task = PublishTask(
            content_master_id=master.id,
            content_id=None,
            platform_id=plat.id,
            account_id=account.id,
            region=getattr(plat, "region", None) or "cn",
            primary_url=primary_url,
            secondary_url=secondary_url,
            status="pending",
        )
        db.add(task)
        db.flush()
        task_ids.append(task.id)

    if not task_ids:
        return error_response(400, "无可用平台账号，请先配置 platform_accounts")

    master.status = "ready"
    db.commit()
    return success_response(
        data={
            "master_id": master.id,
            "task_ids": task_ids,
            "count": len(task_ids),
        },
        message=f"已创建 {len(task_ids)} 条发布任务",
    )
