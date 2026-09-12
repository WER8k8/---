"""养号执行 Worker — 通过 AiToEarn API 自动执行点赞/评论/关注。

将 NurtureCycle 中 pending 的互动记录实际发送到 AiToEarn 平台执行，
并回写执行结果。频控由 social_nurture_service.rate_limit_check 保证。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

def _safe_asyncio_run(coro):
    """_safe_asyncio_run。

    参数说明：
    :param coro: 参数 coro
    :return: 返回处理结果。
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)

async def _execute_like(
    *,
    account_id: str,
    target_post_id: str,
    platform: str = "",
) -> dict[str, Any]:
    """通过 AiToEarn 执行点赞。"""
    from app.services.aitoearn_publish_adapter import like_post
    result = await like_post(
        account_id=account_id,
        post_id=target_post_id,
        platform=platform,
    )
    return result

async def _execute_comment(
    *,
    account_id: str,
    target_post_id: str,
    content: str,
    platform: str = "",
) -> dict[str, Any]:
    """通过 AiToEarn 执行评论。"""
    from app.services.aitoearn_publish_adapter import reply_comment
    result = await reply_comment(
        account_id=account_id,
        comment_id=target_post_id,
        content=content,
        post_id=target_post_id,
    )
    return result

async def _execute_follow(
    *,
    account_id: str,
    target_user_id: str,
    platform: str = "",
) -> dict[str, Any]:
    """通过 AiToEarn 执行关注。"""
    from app.services.aitoearn_publish_adapter import follow_user
    result = await follow_user(
        account_id=account_id,
        target_user_id=target_user_id,
        platform=platform,
    )
    return result

def _get_pending_engagements(
    db: Session, *, limit: int = 30
) -> list[dict[str, Any]]:
    """获取待执行的互动记录。"""
    from app.models.nurture_cycle import EngagementRecord
    rows = (
        db.query(EngagementRecord)
        .filter(EngagementRecord.status == "pending")
        .order_by(EngagementRecord.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "tenant_id": str(r.tenant_id) if r.tenant_id else None,
            "platform": r.platform,
            "platform_account_id": str(r.platform_account_id) if r.platform_account_id else None,
            "action_type": r.action_type,
            "target_post_id": r.target_post_id,
            "target_author": r.target_author,
            "content": r.content,
            "nurture_cycle_id": str(r.nurture_cycle_id) if r.nurture_cycle_id else None,
        }
        for r in rows
    ]

def _resolve_account_id(db: Session, platform_account_id: str | None) -> str | None:
    """从 PlatformAccount 解析出 AiToEarn account_id。"""
    if not platform_account_id:
        return None
    from app.models.platform_registry import PlatformAccount
    acc = db.query(PlatformAccount).filter(PlatformAccount.id == platform_account_id).first()
    if not acc:
        return None
    # 优先取 bound_external_id（即 AiToEarn account_id）
    if getattr(acc, "bound_external_id", None):
        return str(acc.bound_external_id)
    # 回退：从 token_data 取
    td = getattr(acc, "token_data", None)
    if isinstance(td, dict) and td.get("aitoearn_account_id"):
        return str(td["aitoearn_account_id"])
    return None

def _mark_engagement_result(
    db: Session,
    *,
    engagement_id: str,
    success: bool,
    error_message: str | None = None,
) -> None:
    """_mark_engagement_result。

    参数说明：
    :param db: 参数 db
    :param engagement_id: 参数 engagement_id
    :param success: 参数 success
    :param error_message: 参数 error_message
    :return: 返回处理结果。
    """
    from app.models.nurture_cycle import EngagementRecord
    row = (
        db.query(EngagementRecord)
        .filter(EngagementRecord.id == engagement_id)
        .first()
    )
    if not row:
        return
    row.status = "success" if success else "failed"
    row.error_message = error_message
    db.commit()

async def execute_pending_engagements(*, limit: int = 30) -> dict[str, Any]:
    """执行所有待处理的互动任务（点赞/评论/关注）。

    由定时调度器周期性调用（建议每 5~15 分钟一次）。
    """
    from app.services.aitoearn_publish_adapter import aitoearn_enabled
    if not aitoearn_enabled():
        return {"skipped": True, "reason": "AITOEARN_API_KEY 未配置", "executed": 0}

    db: Session = SessionLocal()
    executed = 0
    succeeded = 0
    failed = 0
    try:
        pending = _get_pending_engagements(db, limit=limit)
        await _process_engagement_items()
    finally:
        db.close()

    return {
        "executed": executed,
        "succeeded": succeeded,
        "failed": failed,
    }

async def _process_engagement_items():
    """遍历待执行互动记录，逐条执行并回写结果。

    注意：pending/db 等由调用方作用域提供，本函数保持原自由变量引用语义。
    """
    for item in pending:
        await _process_single_engagement(db, item)


async def _process_single_engagement(db: Session, item: dict[str, Any]) -> None:
    """执行单条互动：解析账号→频控→按类型分发→回写执行结果。"""
    engagement_id = item["id"]
    action_type = item["action_type"]
    account_id = _resolve_account_id(db, item.get("platform_account_id"))
    if not account_id:
        _mark_engagement_result(
            db,
            engagement_id=engagement_id,
            success=False,
            error_message="无法解析 AiToEarn account_id",
        )
        return

    # 频控检查
    cycle_id = item.get("nurture_cycle_id")
    if cycle_id:
        from app.services.social_nurture_service import rate_limit_check
        check = rate_limit_check(db, cycle_id=cycle_id, action_type=action_type)
        if not check.get("allowed"):
            logger.debug(
                "engagement %s rate-limited: %s",
                engagement_id,
                check.get("reason"),
            )
            return

    try:
        result = await _dispatch_engagement_action(db, item, account_id)
        if result is _UNSUPPORTED_ACTION:
            return
        ok = not (isinstance(result, dict) and result.get("success") is False)
        _mark_engagement_result(
            db,
            engagement_id=engagement_id,
            success=ok,
            error_message=None if ok else str(result)[:500],
        )
        if ok:
            cycle_id = item.get("nurture_cycle_id")
            if cycle_id:
                from app.services.social_nurture_service import record_action
                record_action(db, cycle_id=cycle_id, action_type=action_type)
    except Exception as exc:
        logger.error("engagement %s execution failed: %s", engagement_id, exc)
        _mark_engagement_result(
            db,
            engagement_id=engagement_id,
            success=False,
            error_message=str(exc)[:500],
        )


class _UnsupportedAction:
    """标记不支持的互动类型，避免与真实执行结果混淆。"""
    pass


_UNSUPPORTED_ACTION = _UnsupportedAction()


async def _dispatch_engagement_action(db: Session, item: dict[str, Any], account_id: str):
    """按 action_type 分发到点赞/评论/关注执行，不支持则返回 _UNSUPPORTED_ACTION。"""
    action_type = item["action_type"]
    if action_type == "like":
        return await _execute_like(
            account_id=account_id,
            target_post_id=item.get("target_post_id") or "",
            platform=item.get("platform", ""),
        )
    if action_type in ("comment", "reply"):
        return await _execute_comment(
            account_id=account_id,
            target_post_id=item.get("target_post_id") or "",
            content=item.get("content") or "",
            platform=item.get("platform", ""),
        )
    if action_type == "follow":
        return await _execute_follow(
            account_id=account_id,
            target_user_id=item.get("target_author") or item.get("target_post_id") or "",
            platform=item.get("platform", ""),
        )
    _mark_engagement_result(
        db,
        engagement_id=item["id"],
        success=False,
        error_message=f"不支持的互动类型: {action_type}",
    )
    return _UNSUPPORTED_ACTION

def execute_pending_engagements_sync(**kwargs: Any) -> dict[str, Any]:
    """execute_pending_engagements_sync。

    参数说明：
    :param **kwargs: 参数 **kwargs
    :return: 返回处理结果。
    """
    return _safe_asyncio_run(execute_pending_engagements(**kwargs))
