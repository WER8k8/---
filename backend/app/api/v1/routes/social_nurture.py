"""海外养号周期 API（持久化 + 频控 + 互动管理）。"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import error_response, success_response
from app.core.security import get_current_user
from app.core.tenant_access import assert_user_tenant_active, is_platform_admin, is_tenant_staff
from app.models.user import User
from app.services import social_nurture_service as svc
from app.services.tenant_scenario_service import resolve_tenant_id_for_user


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/social-nurture"
ROUTE_TAGS = ["海外养号"]

router = APIRouter()


def _guard_nurture_read(user: User, db: Session):
    """执行 guard_nurture_read 相关逻辑处理。
    
    :param user: 用户对象
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    if is_platform_admin(user):
        return None
    if is_tenant_staff(user):
        try:
            assert_user_tenant_active(user, db)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning("租户状态检查失败: %s", e)
            return error_response(403, "未关联租户或租户已冻结")
        return None
    return error_response(403, "权限不足")


def _guard_nurture_write(user: User, db: Session):
    """执行 guard_nurture_write 相关逻辑处理。
    
    :param user: 用户对象
    :param db: 数据库会话
    :return: 返回处理结果。
    """
    if user.role in ("admin", "super_admin", "tenant_admin"):
        return _guard_nurture_read(user, db)
    return error_response(403, "权限不足")


def _tenant_scope(db: Session, user: User, explicit: str | None = None) -> str | None:
    """执行 tenant_scope 相关逻辑处理。
    
    :param db: 数据库会话
    :param user: 用户对象
    :param explicit: 参数 explicit
    :return: 返回处理结果。
    """
    if is_platform_admin(user):
        return explicit
    return resolve_tenant_id_for_user(db, user)


# ---- 养号周期 CRUD ----

class NurtureCreateBody(BaseModel):
    tenant_id: str | None = None
    platform: str = Field(..., min_length=2, max_length=32)
    account_label: str = Field(..., min_length=1, max_length=120)
    platform_account_id: str | None = None
    notes: str = ""
    rules: dict[str, Any] | None = None


class NurtureTransitionBody(BaseModel):
    status: str = Field(..., description="warming|active|cooling|paused|draft|archived")
    notes: str | None = None


@router.get("/rules")
def get_nurture_rules(
    platform: str | None = None,
    region: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """各平台默认养号规则（含频控参数）。"""
    _ = current_user
    if platform:
        rules = svc.get_nurture_profile(platform)
        return success_response(data={"platform": platform, "region": region, "rules": rules})

    summary = {}
    for name, profile in svc.PLATFORM_NURTURE_PROFILES.items():
        summary[name] = {
            "warmup_days": profile.get("warmup_days"),
            "daily_posts": profile.get("daily_posts"),
            "post_interval_min_hours": profile.get("post_interval_min_hours"),
            "max_posts_per_hour": profile.get("max_posts_per_hour"),
        }
    return success_response(data={"profiles": summary})


@router.get("/cycles")
def list_nurture_cycles(
    tenant_id: str | None = None,
    platform: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /cycles 请求，列出相关资源。
    
    :param tenant_id: 租户ID
    :param platform: 参数 platform
    :param status: 状态
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_nurture_read(current_user, db)
    if denied:
        return denied
    tid = _tenant_scope(db, current_user, tenant_id)
    items = svc.list_cycles(db, tenant_id=tid, platform=platform, status=status)
    return success_response(data={"items": items, "total": len(items)})


@router.post("/cycles")
def create_nurture_cycle(
    body: NurtureCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /cycles 请求，创建相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_nurture_write(current_user, db)
    if denied:
        return denied
    tid = _tenant_scope(db, current_user, body.tenant_id)
    cycle = svc.create_cycle(
        db,
        tenant_id=tid,
        platform=body.platform,
        account_label=body.account_label,
        platform_account_id=body.platform_account_id,
        notes=body.notes,
        rules=body.rules,
    )
    return success_response(data=cycle, message="养号周期已创建")


@router.post("/cycles/{cycle_id}/transition")
def transition_nurture_cycle(
    cycle_id: str,
    body: NurtureTransitionBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /cycles/{cycle_id}/transition 请求，transition相关资源。
    
    :param cycle_id: 参数 cycle_id
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_nurture_write(current_user, db)
    if denied:
        return denied
    try:
        cycle = svc.transition_cycle(db, cycle_id=cycle_id, new_status=body.status, notes=body.notes)
    except KeyError:
        return error_response(404, "周期不存在")
    except ValueError as e:
        return error_response(400, str(e))
    return success_response(data=cycle, message="状态已更新")


@router.post("/cycles/{cycle_id}/check")
def check_publish_allowed(
    cycle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查养号周期是否允许发布。"""
    _ = current_user
    result = svc.can_publish_now(db, cycle_id=cycle_id)
    return success_response(data=result)


@router.post("/cycles/{cycle_id}/advance")
def auto_advance_cycle(
    cycle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发自动升级检查（通常由定时任务执行）。"""
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "权限不足")
    result = svc.auto_advance(db, cycle_id)
    if result is None:
        return success_response(data={"message": "无需升级"})
    return success_response(data=result, message="养号状态已检查")


@router.post("/worker/tick")
async def run_nurture_worker_tick(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """超管手动触发养号全链路 tick（计划 + 互动 + 定时发布 + 升级）。"""
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "权限不足")

    from app.services.nurture_execution_worker import execute_pending_engagements
    from app.tasks.scheduled_publish_worker import (
        auto_advance_all_nurture_cycles,
        dispatch_pending_scheduled_publishes,
    )
    plan = svc.plan_daily_engagements(db, limit=40)
    publish = await dispatch_pending_scheduled_publishes()
    engage = await execute_pending_engagements(limit=30)
    advance = await auto_advance_all_nurture_cycles()
    return success_response(
        data={"plan": plan, "publish": publish, "engage": engage, "advance": advance},
        message="养号 worker tick 完成",
    )


# ---- 定时发布 ----

class SchedulePublishBody(BaseModel):
    platform_name: str
    title: str
    body: str = ""
    video_url: str | None = None
    cover_url: str | None = None
    tags: list[str] | None = None
    scheduled_at: datetime | None = None
    tenant_id: str | None = None
    platform_account_id: str | None = None
    content_master_id: str | None = None


@router.post("/schedule")
def create_scheduled_publish(
    body: SchedulePublishBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 POST /schedule 请求，创建相关资源。
    
    :param body: 请求体
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_nurture_write(current_user, db)
    if denied:
        return denied
    tid = _tenant_scope(db, current_user, body.tenant_id)
    result = svc.schedule_publish(
        db,
        tenant_id=tid,
        platform_name=body.platform_name,
        title=body.title,
        body=body.body,
        video_url=body.video_url,
        cover_url=body.cover_url,
        tags=body.tags,
        scheduled_at=body.scheduled_at,
        platform_account_id=body.platform_account_id,
        content_master_id=body.content_master_id,
    )
    return success_response(data=result, message="定时发布已创建")


@router.get("/schedule/pending")
def list_pending_scheduled(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /schedule/pending 请求，列出相关资源。
    
    :param limit: 返回条数上限
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    if current_user.role not in ("admin", "super_admin"):
        return error_response(403, "权限不足")
    items = svc.get_pending_scheduled(db, limit=limit)
    return success_response(data={"items": items, "total": len(items)})


# ---- 互动管理 ----

class EngagementRecordBody(BaseModel):
    platform: str
    action_type: str = Field(..., description="like|comment|follow|reply|share")
    target_post_id: str | None = None
    target_author: str | None = None
    content: str | None = None
    nurture_cycle_id: str | None = None
    platform_account_id: str | None = None


@router.post("/engagement")
def create_engagement(
    body: EngagementRecordBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """记录互动操作（点赞/评论/关注/回复）。"""
    denied = _guard_nurture_write(current_user, db)
    if denied:
        return denied
    tid = _tenant_scope(db, current_user, None)
    result = svc.record_engagement(
        db,
        tenant_id=tid,
        platform=body.platform,
        action_type=body.action_type,
        target_post_id=body.target_post_id,
        target_author=body.target_author,
        content=body.content,
        nurture_cycle_id=body.nurture_cycle_id,
        platform_account_id=body.platform_account_id,
    )
    return success_response(data=result, message="互动记录已创建")


@router.get("/engagement")
def list_engagement_records(
    tenant_id: str | None = None,
    platform: str | None = None,
    action_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理 GET /engagement 请求，列出相关资源。
    
    :param tenant_id: 租户ID
    :param platform: 参数 platform
    :param action_type: 参数 action_type
    :param limit: 返回条数上限
    :param db: 数据库会话
    :param current_user: 当前登录用户
    :return: 返回处理结果。
    """
    denied = _guard_nurture_read(current_user, db)
    if denied:
        return denied
    tid = _tenant_scope(db, current_user, tenant_id)
    items = svc.list_engagements(
        db, tenant_id=tid, platform=platform, action_type=action_type, limit=limit
    )
    return success_response(data={"items": items, "total": len(items)})
