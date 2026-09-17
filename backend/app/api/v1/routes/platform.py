# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""多平台分发 API 路由 - 平台账号管理、内容分发、会话保持"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import user_has_module_permission
from app.db.session import get_db
from app.models.content import Platform, PlatformAccount, PublishLog, PublishTask
from app.models.user import User
from app.services.platform_catalog import (
    PILOT_CN_NAMES,
    PILOT_GLOBAL_NAMES,
    PLATFORMS_CN,
    PLATFORMS_GLOBAL,
    catalog_summary,
)
from app.services.platform_alignment_service import alignment_report
from app.services.publish_service import PublishService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = ""

router = APIRouter(prefix="/platforms", tags=["多平台分发"])


# ==================== Pydantic 模型 ====================

class ConnectPlatformBody(BaseModel):
    account_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    cookie_data: Optional[str] = None
    token_data: Optional[dict] = None
    token_expire_at: Optional[str] = None
    configs: Optional[dict] = None


class PublishContentBody(BaseModel):
    content_id: str = Field(..., description="内容ID")
    platform_ids: List[str] = Field(..., min_length=1, description="目标平台ID列表")
    account_ids: List[str] = Field(..., min_length=1, description="发布账号ID列表")
    publish_type: str = Field(default="immediate", description="发布类型: immediate / scheduled / batch")
    scheduled_time: Optional[str] = None


class BatchPublishItem(BaseModel):
    content_id: str
    platform_ids: List[str]
    account_ids: List[str]
    publish_type: str = "immediate"
    scheduled_time: Optional[str] = None


class BatchPublishBody(BaseModel):
    tasks: List[BatchPublishItem] = Field(..., min_length=1)


class SchedulePublishBody(BaseModel):
    content_id: str
    platform_ids: List[str]
    account_ids: List[str]
    scheduled_time: str = Field(..., description="ISO 格式定时时间")


# ==================== 平台列表 ====================


@router.get("")
def list_platforms(db: Session = Depends(get_db)):
    """获取所有平台列表"""
    platforms = db.query(Platform).filter_by(is_active=True).all()
    result = []
    for p in platforms:
        account_count = db.query(PlatformAccount).filter_by(
            platform_id=p.id, is_active=True).count()
        result.append({
            "id": p.id,
            "name": p.name,
            "platform_type": p.platform_type,
            "icon": p.icon,
            "base_url": p.base_url,
            "region": getattr(p, "region", None) or "cn",
            "content_type": getattr(p, "content_type", None) or "article",
            "has_api": p.has_api,
            "account_count": account_count,
        })
    return success_response(data=result)


@router.get("/catalog/alignment")
def platform_catalog_alignment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """P1-10：catalog 与 DB 对齐报告。"""
    from app.services.platform_alignment_service import alignment_report
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "仅超管可查看对齐报告")
    return success_response(data=alignment_report(db))


@router.get("/catalog")
def platform_catalog(db: Session = Depends(get_db)):
    """40 平台目录摘要（国内 20 + 海外 20 目标）。"""
    summary = catalog_summary(db)
    return success_response(
        data={
            **summary,
            "catalog_cn": [n for n, *_ in PLATFORMS_CN],
            "catalog_global": [n for n, *_ in PLATFORMS_GLOBAL],
        }
    )


@router.get("/rank-priority")
def platform_rank_priority(
    region: Optional[str] = Query(None, description="cn | global"),
    live_only: bool = Query(False),
    limit: int = Query(12, ge=1, le=40),
):
    """排名优先：建议发布顺序（GEO 权重 × 适配器状态）。"""
    from app.services.geo.platform_rank_registry import (
        all_platform_rank_profiles,
        publish_order_for_ranking,
        revenue_loop_kpi_labels,
    )
    profiles = all_platform_rank_profiles()
    if region in ("cn", "global"):
        profiles = [p for p in profiles if p.region == region]
    return success_response(
        data={
            "publish_order": publish_order_for_ranking(
                region=region, live_only=live_only, limit=limit
            ),
            "profiles": [
                {
                    "name": p.name,
                    "geo_weight": p.geo_weight,
                    "adapter_status": p.adapter_status,
                    "rank_score": p.rank_score,
                    "rank_priority": p.rank_priority,
                    "region": p.region,
                }
                for p in profiles[:limit]
            ],
            "revenue_loop": revenue_loop_kpi_labels(),
            "principle": "平台覆盖面 ↑ → GEO 引用面 ↑ → 询盘电话 ↑ → 开户与续费",
        }
    )


@router.get("/discovery")
def platform_discovery(
    db: Session = Depends(get_db),
):
    """平台发现：catalog 与 live 适配器缺口，下一批建设队列。"""
    from app.services.geo.platform_discovery_service import discovery_snapshot
    return success_response(data=discovery_snapshot(db))


@router.get("/pilot")
def list_pilot_platforms(db: Session = Depends(get_db)):
    """5+10 试点平台：国内 5 + 海外十大社交/IM（PM 总册扩展）。"""
    pilot_names = set(PILOT_CN_NAMES) | set(PILOT_GLOBAL_NAMES)
    platforms = (
        db.query(Platform)
        .filter(Platform.is_active, Platform.name.in_(pilot_names))
        .all()
    )
    cn = [p for p in platforms if (p.region or "cn") == "cn"]
    global_ = [p for p in platforms if (p.region or "cn") == "global"]
    def _row(p: Platform) -> dict:
        """执行 row 相关逻辑处理。
        
        :param p: 参数 p
        :return: 返回处理结果。
        """
        return {
            "id": p.id,
            "name": p.name,
            "region": p.region or "cn",
            "content_type": p.content_type or "article",
            "platform_type": p.platform_type,
            "base_url": p.base_url,
        }

    return success_response(
        data={
            "pilot": True,
            "total": len(platforms),
            "target_total": len(pilot_names),
            "cn": [_row(p) for p in cn],
            "global": [_row(p) for p in global_],
            "global_social_10": list(PILOT_GLOBAL_NAMES),
            "ready_for_publish": len(platforms) >= len(pilot_names),
        }
    )


# ==================== 平台账号管理 ====================


@router.post("/{platform_id}/connect")
def connect_platform(
    platform_id: str,
    body: ConnectPlatformBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """连接平台账号"""
    service = PublishService(db)
    try:
        account = service.connect_platform(
            platform_id=platform_id,
            account_data=body.model_dump(exclude_none=True),
        )
        return success_response(
            data={
                "id": account.id,
                "account_name": account.account_name,
                "login_status": account.login_status,
            },
            message="平台账号连接成功",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.post("/{platform_id}/disconnect")
def disconnect_platform(
    platform_id: str,
    account_id: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """断开平台账号连接"""
    service = PublishService(db)
    try:
        service.disconnect_platform(account_id)
        return success_response(message="平台账号已断开")
    except ValueError as e:
        return error_response(404, str(e))


# ==================== 账号列表与状态管理 ====================


@router.get("/accounts")
def list_accounts(
    platform_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """已连接账号列表及状态"""
    service = PublishService(db)
    accounts = service.list_accounts(platform_id=platform_id)
    return success_response(data=accounts)


@router.post("/accounts/{account_id}/refresh")
def refresh_account_session(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刷新会话"""
    service = PublishService(db)
    try:
        account = service.refresh_session(account_id)
        return success_response(
            data={
                "id": account.id,
                "login_status": account.login_status,
                "last_login_at": account.last_login_at,
            },
            message="会话已刷新",
        )
    except ValueError as e:
        return error_response(404, str(e))


@router.get("/accounts/{account_id}/check")
def check_account_session(
    account_id: str,
    db: Session = Depends(get_db),
):
    """检查会话是否有效"""
    service = PublishService(db)
    try:
        result = service.check_session(account_id)
        return success_response(data=result)
    except ValueError as e:
        return error_response(404, str(e))


@router.post("/accounts/{account_id}/relogin")
def auto_relogin_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """自动重新登录"""
    service = PublishService(db)
    try:
        result = service.auto_relogin(account_id)
        if result["success"]:
            return success_response(data=result, message="自动重登成功")
        return success_response(data=result, message="自动重登失败，可能需要人工介入")
    except ValueError as e:
        return error_response(404, str(e))


# ==================== 内容发布 ====================


@router.post("/publish")
def publish_content(
    body: PublishContentBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """一键发布内容到多个平台"""
    if not user_has_module_permission(current_user, "content", "publish"):
        return error_response(403, "缺少 content:publish 权限")
    service = PublishService(db)
    sched = None
    if body.scheduled_time:
        try:
            sched = datetime.fromisoformat(
                body.scheduled_time.replace("Z", "+00:00"))
        except (ValueError, TypeError, Exception) as e:
            logger = logging.getLogger(__name__)
            logger.warning("定时时间解析失败: %s", e)
            return error_response(400, "定时时间格式无效，请使用 ISO 8601 格式")

    try:
        result = service.publish_content(
            content_id=body.content_id,
            platform_ids=body.platform_ids,
            account_ids=body.account_ids,
            publish_type=body.publish_type,
            scheduled_time=sched,
        )
        return success_response(
            data=result,
            message=f"成功创建 {result['task_count']} 个发布任务",
        )
    except ValueError as e:
        return error_response(400, str(e))


@router.post("/publish/batch")
def batch_publish(
    body: BatchPublishBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量发布"""
    service = PublishService(db)
    results = service.batch_publish(
        [t.model_dump() for t in body.tasks]
    )
    total = sum(r.get("task_count", 0) for r in results)
    return success_response(
        data={"results": results, "total_tasks": total},
        message=f"批量发布完成，共 {total} 个任务",
    )


@router.post("/publish/schedule")
async def schedule_publish(
    body: SchedulePublishBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """定时发布"""
    service = PublishService(db)
    try:
        sched = datetime.fromisoformat(
            body.scheduled_time.replace("Z", "+00:00"))
    except (ValueError, TypeError, Exception) as e:
        logger = logging.getLogger(__name__)
        logger.warning("定时时间解析失败: %s", e)
        return error_response(400, "定时时间格式无效，请使用 ISO 8601 格式")

    try:
        result = await service.schedule_publish(
            content_id=body.content_id,
            platform_ids=body.platform_ids,
            account_ids=body.account_ids,
            scheduled_time=sched,
        )
        return success_response(
            data=result,
            message=f"定时发布已设置，共 {result['task_count']} 个任务",
        )
    except ValueError as e:
        return error_response(400, str(e))


# ==================== 发布任务管理 ====================


@router.get("/publish/tasks")
def list_publish_tasks(
    status: Optional[str] = Query(None),
    platform_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    content_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布任务列表"""
    service = PublishService(db)
    items, total = service.get_publish_tasks(
        status=status,
        platform_id=platform_id,
        account_id=account_id,
        content_id=content_id,
        page=page,
        page_size=page_size,
    )
    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/publish/tasks/{task_id}/retry")
def retry_publish_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重试发布任务"""
    task = db.query(PublishTask).filter_by(id=task_id).first()
    if not task:
        return error_response(404, "发布任务不存在")

    task.status = "pending"
    task.retry_count = (task.retry_count or 0) + 1
    db.commit()
    # 触发重新执行
    service = PublishService(db)
    service._execute_publish_tasks([task_id])
    return success_response(message="已重新执行")


@router.delete("/publish/tasks/{task_id}")
def delete_publish_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除发布任务"""
    task = db.query(PublishTask).filter_by(id=task_id).first()
    if not task:
        return error_response(404, "发布任务不存在")

    # 连带删除日志
    db.query(PublishLog).filter_by(task_id=task_id).delete()
    db.delete(task)
    db.commit()
    return success_response(message="已删除")


# ==================== 发布日志 ====================


@router.get("/publish/logs")
def list_publish_logs(
    task_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布日志"""
    service = PublishService(db)
    items, total = service.get_publish_logs(
        task_id=task_id,
        level=level,
        page=page,
        page_size=page_size,
    )
    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


# ==================== 会话保持（运维） ====================


@router.post("/keepalive")
def keepalive_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发会话保持检查（运维操作）"""
    service = PublishService(db)
    result = service.keepalive_checker()
    return success_response(data=result, message="会话保持检查完成")


@router.get("/stats")
def publish_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布统计"""
    service = PublishService(db)
    stats = service.get_publish_stats()
    return success_response(data=stats)
