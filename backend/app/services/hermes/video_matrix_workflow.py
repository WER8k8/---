"""Hermes 视频矩阵真发编排 — 预检 → 分发 → 验真汇总。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services.hermes.brand_guard import sanitize_public_copy, sanitize_public_data
from app.services.publish_workers.tier_router import preflight_workers
from app.services.video_publish_router import distribute_video

logger = logging.getLogger(__name__)


def _step(label: str, status: str, **extra: Any) -> dict[str, Any]:
    """_step。

    参数说明：
    :param label: 参数 label
    :param status: 参数 status
    :param **extra: 参数 **extra
    :return: 返回处理结果。
    """
    return {"label": label, "status": status, **extra}


def run_video_matrix_v1(
    db: Session,
    *,
    tenant_id: str,
    message: str,
    user_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Hermes 工作流：视频矩阵真发。
    context 需含 media_task_id；可选 platform_ids、include_tenant_site。
    """
    ctx = dict(context or {})
    media_task_id = (ctx.get("media_task_id") or "").strip()
    platform_ids = ctx.get("platform_ids") or []
    include_tenant_site = ctx.get("include_tenant_site", True)
    scheduled_at = ctx.get("scheduled_at")
    scheduled_dt = None
    if scheduled_at:
        from datetime import datetime
        if isinstance(scheduled_at, datetime):
            scheduled_dt = scheduled_at
        elif isinstance(scheduled_at, str):
            scheduled_dt = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
    errors: list[str] = []
    steps: list[dict[str, Any]] = []
    preflight = preflight_workers()
    ret = _video_matrix_run_guards(ctx, steps, media_task_id, preflight)
    if ret is not None:
        return ret

    distribute_result, verified, unverified = _run_video_distribution(
        db,
        tenant_id=tenant_id,
        media_task_id=media_task_id,
        platform_ids=platform_ids,
        include_tenant_site=include_tenant_site,
        scheduled_dt=scheduled_dt,
        steps=steps,
        errors=errors,
    )
    reply = _build_reply(
        message=message,
        distribute_result=distribute_result,
        verified=verified,
        unverified=unverified,
        errors=errors,
    )
    return sanitize_public_data(
        {
            "workflow": "video_matrix_v1",
            "ticket_id": media_task_id,
            "steps": steps,
            "preflight": preflight,
            "distribute": distribute_result,
            "verified_posts": [
                {
                    "platform": r.get("platform_name"),
                    "url": r.get("platform_post_url"),
                    "via": r.get("via"),
                    "tier": r.get("tier"),
                }
                for r in verified
            ],
            "needs_confirmation": bool(unverified),
            "human_review_required": bool(unverified),
            "errors": errors,
            "reply": reply,
        }
    )


def _build_reply(
    *,
    message: str,
    distribute_result: dict[str, Any],
    verified: list[dict[str, Any]],
    unverified: list[dict[str, Any]],
    errors: list[str],
) -> str:
    """_build_reply。

    参数说明：
    :param message: 参数 message
    :param distribute_result: 参数 distribute_result
    :param verified: 参数 verified
    :param unverified: 参数 unverified
    :param errors: 参数 errors
    :return: 返回处理结果。
    """
    del message
    lines = ["【视频矩阵 · Hermes 编排】分发结果："]
    site = distribute_result.get("tenant_site") or {}
    if site.get("published"):
        lines.append(f"• 租户官网：已登记 {site.get('url') or '视频页'}")

    if verified:
        lines.append(f"• 外站验真成功 {len(verified)} 个：")
        for r in verified[:6]:
            pname = r.get("platform_name") or "平台"
            url = r.get("platform_post_url") or r.get("platform_post_id") or ""
            via = r.get("via") or r.get("tier") or ""
            lines.append(f"  - {pname}（{via}）：{url}")

    if unverified:
        lines.append(f"• 未验真 / 失败 {len(unverified)} 个：")
        for r in unverified[:4]:
            pname = r.get("platform_name") or "平台"
            err = (r.get("error_message") or "无作品链接")[:120]
            lines.append(f"  - {pname}：{err}")

    if not verified and not unverified:
        lines.append("• 未选择外站平台，仅处理租户官网。")

    lines.append("\n成功标准：必须返回可点击作品链接；无链接一律不算成功。")
    if errors:
        lines.append(f"\n告警：{'；'.join(errors[:2])}")
    return sanitize_public_copy("\n".join(lines))

def _run_video_distribution(
    db: Session,
    *,
    tenant_id: str,
    media_task_id: str,
    platform_ids: list[Any],
    include_tenant_site: bool,
    scheduled_dt: Any,
    steps: list[dict[str, Any]],
    errors: list[str],
) -> tuple[dict[str, Any], list[Any], list[Any]]:
    """_run_video_distribution。

    参数说明：
    :return: 返回 (distribute_result, verified, unverified)。
    """
    # ② 统一分发（内含多 Worker 链 + 验真）
    steps.append(_step("视频真发分发", "running", media_task_id=media_task_id))
    distribute_result: dict[str, Any] = {}
    try:
        # 安全执行异步函数：兼容已有事件循环（FastAPI）和无事件循环（Celery）
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _run_distribute():
            """_run_distribute。
            :return: 返回处理结果。
            """
            return await distribute_video(
                db,
                media_task_id=media_task_id,
                platform_ids=platform_ids or None,
                include_tenant_site=include_tenant_site,
                tenant_id=tenant_id,
                scheduled_at=scheduled_dt,
            )

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                distribute_result = pool.submit(asyncio.run, _run_distribute()).result()
        else:
            distribute_result = asyncio.run(_run_distribute())
        summary = distribute_result.get("summary") or {}
        ok_count = summary.get("succeeded", 0)
        fail_count = summary.get("failed", 0)
        steps[-1] = _step(
            "视频真发分发",
            "done" if ok_count else "failed",
            succeeded=ok_count,
            failed=fail_count,
            hermes_orchestration=distribute_result.get("hermes_orchestration"),
        )
    except Exception as exc:
        logger.warning("hermes video matrix distribute failed: %s", exc)
        steps[-1] = _step("视频真发分发", "failed", error=str(exc)[:300])
        errors.append(str(exc))

    # ③ 逐平台验真汇总
    platform_rows = distribute_result.get("results") or []
    verified = [r for r in platform_rows if r.get("success") and r.get("verified")]
    unverified = [r for r in platform_rows if not r.get("success")]
    steps.append(
        _step(
            "验真汇总",
            "done" if verified and not unverified else ("partial" if verified else "failed"),
            verified_count=len(verified),
            failed_count=len(unverified),
            platforms=[r.get("platform_name") for r in platform_rows],
        )
    )
    return distribute_result, verified, unverified


def _video_matrix_run_guards(
    ctx: dict[str, Any],
    steps: list[dict[str, Any]],
    media_task_id: str,
    preflight: dict[str, Any],
) -> dict[str, Any] | None:
    """_video_matrix_run_guards。

    参数说明：
    :return: 返回处理结果（或 None 表示放行）。
    """
    # ① Worker 预检
    steps.append(_step("发布 Worker 预检", "running"))
    workers = preflight.get("workers") or {}
    if not preflight.get("ready"):
        steps[-1] = _step(
            "发布 Worker 预检",
            "failed",
            detail="无可用 Worker",
            workers=workers,
        )
        reply = (
            "【视频矩阵】当前环境未就绪：请至少配置一种真发 Worker"
            "（SAU / biliup / 小红书 MCP / AiToEarn Key）。"
        )
        return sanitize_public_data(
            {
                "workflow": "video_matrix_v1",
                "steps": steps,
                "preflight": preflight,
                "needs_confirmation": False,
                "errors": ["无可用 Worker"],
                "reply": sanitize_public_copy(reply),
            }
        )
    enabled = [k for k, v in workers.items() if isinstance(v, dict) and v.get("enabled")]
    steps[-1] = _step("发布 Worker 预检", "done", enabled_workers=enabled)
    if not ctx.get("human_confirmed"):
        platforms = ctx.get("platforms") or ["抖音", "视频号", "百家号"]
        steps.append(_step("人工确认门", "pending", platforms=platforms))
        return sanitize_public_data(
            {
                "workflow": "video_matrix_v1",
                "steps": steps,
                "preflight": preflight,
                "needs_confirmation": True,
                "human_review_required": True,
                "publish_plan": {
                    "platforms": platforms,
                    "media_task_id": media_task_id or None,
                    "cta": ctx.get("cta") or "导向独立域询盘表单/电话",
                },
                "errors": [],
                "reply": sanitize_public_copy(
                    "【视频矩阵】发布计划已就绪。真发前须人工确认："
                    "请在 context 设置 human_confirmed=true 并传入 media_task_id。"
                ),
            }
        )

    if not media_task_id:
        steps.append(_step("视频分发", "failed", error="缺少 media_task_id"))
        return sanitize_public_data(
            {
                "workflow": "video_matrix_v1",
                "steps": steps,
                "preflight": preflight,
                "needs_confirmation": False,
                "errors": ["context.media_task_id 必填"],
                "reply": sanitize_public_copy(
                    "【视频矩阵】请在 context 传入 media_task_id（多媒体工厂任务 ID）。"
                ),
            }
        )
    return None

