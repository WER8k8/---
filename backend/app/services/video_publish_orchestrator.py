# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes 编排的视频真发 — 多 Worker 链式尝试 + 强制验真 + 养号频控。

增强自原版本，新增：
- 发布前养号状态检查（nurture cycle integration）
- 定时发布支持（scheduled publish）
- 发布后互动记录
- 更完善的错误分类与重试策略
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.aitoearn_publish_adapter import publish_video_via_aitoearn
from app.services.publish_workers.biliup_worker import publish_via_biliup
from app.services.publish_workers.media_fetch import download_image_to_temp, download_video_to_temp
from app.services.publish_workers.sau_worker import publish_via_sau
from app.services.publish_workers.dual_line import annotate_failover_result
from app.services.publish_workers.tier_router import platform_tier_chain
from app.services.publish_workers.verify import verify_publish_outcome
from app.services.publish_workers.xhs_mcp_worker import publish_via_xhs_mcp

logger = get_logger(__name__)


async def _try_tier_sau(
    *,
    platform_name: str,
    local_video: Path,
    title: str,
    body: str,
    tags: list[str] | None,
    video_url: str,
    cover_url: str,
    tenant_id: str | None,
    scheduled_at: int | None = None,
) -> dict[str, Any]:
    """SAU Worker 分支：本地视频 + 可选封面下载，用完即清临时封面。

    封面仅在 cover_url 为 http 链接时下载；下载失败不阻断发布，
    仅记录 warning 并继续以无封面方式提交。
    """
    cover_path = None
    owned_cover: Path | None = None
    if cover_url and str(cover_url).strip().startswith("http"):
        try:
            cover_path = await download_image_to_temp(cover_url)
            owned_cover = cover_path
        except Exception as exc:
            logger.warning("sau cover fetch failed: %s", exc)
    try:
        raw = await publish_via_sau(
            platform_name=platform_name,
            local_video=local_video,
            title=title,
            desc=body,
            tags=tags,
            tenant_id=tenant_id,
            scheduled_at=scheduled_at,
            cover_path=cover_path,
            video_url=video_url,
            cover_url=cover_url,
        )
    finally:
        if owned_cover and owned_cover.exists():
            try:
                owned_cover.unlink()
            except OSError:
                pass
    return verify_publish_outcome({**raw, "platform_name": platform_name, "tier": "sau"})


async def _try_tier(
    tier: str,
    *,
    platform_name: str,
    local_video: Path,
    title: str,
    body: str,
    tags: list[str] | None,
    video_url: str,
    cover_url: str,
    tenant_id: str | None,
    allowed_aitoearn_ids: set[str] | None = None,
    scheduled_at: int | None = None,
) -> dict[str, Any]:
    """按 tier 分派到对应发布 Worker，并统一做验真封装。

    当前支持的 Worker 层：
    - sau: 本地视频 + 可选封面下载（临时文件用完即清）
    - biliup: 本地视频直传 bilibili
    - xhs_mcp: 本地视频经 MCP 发布小红书
    - aitoearn: 云端链接直发（不走本地下载）

    所有分支统一以 verify_publish_outcome 校验结果并附加
    platform_name / tier 字段，供上层组装 attempts 轨迹。
    """
    if tier == "sau":
        return await _try_tier_sau(
            platform_name=platform_name,
            local_video=local_video,
            title=title,
            body=body,
            tags=tags,
            video_url=video_url,
            cover_url=cover_url,
            tenant_id=tenant_id,
            scheduled_at=scheduled_at,
        )

    if tier == "biliup":
        raw = await publish_via_biliup(
            local_video=local_video,
            title=title,
            desc=body,
            tags=tags,
        )
        return verify_publish_outcome({**raw, "platform_name": platform_name, "tier": tier})

    if tier == "xhs_mcp":
        raw = await publish_via_xhs_mcp(
            local_video=local_video,
            title=title,
            content=body,
            tags=tags,
        )
        return verify_publish_outcome({**raw, "platform_name": platform_name, "tier": tier})

    if tier == "aitoearn":
        rows = await publish_video_via_aitoearn(
            platform_names={platform_name},
            title=title,
            video_url=video_url,
            cover_url=cover_url,
            topics=tags,
            body=body,
            allowed_account_ids=allowed_aitoearn_ids,
            tenant_id=tenant_id,
            scheduled_at=scheduled_at,
        )
        row = rows[0] if rows else {}
        mapped = {
            "platform_name": platform_name,
            "tier": tier,
            "via": "aitoearn",
            "platform_post_url": row.get("platform_post_url"),
            "platform_post_id": row.get("platform_post_id"),
            "flow_id": row.get("flow_id"),
            "pending": row.get("pending"),
            "error_message": row.get("error_message"),
            "success": bool(row.get("success")),
        }
        return verify_publish_outcome(mapped)

    return {
        "success": False,
        "platform_name": platform_name,
        "tier": tier,
        "error_message": f"未知 Worker 层: {tier}",
    }


async def _check_video_chain_gate(
    *,
    tenant_id: str | None,
    title: str,
    body: str,
) -> Any:
    """视频链路双关卡检查，异常或未租户时返回 None。"""
    if not tenant_id:
        return None
    try:
        from app.services.pipeline.chains import gate_content  # noqa: PLC0415
        return gate_content(
            None,
            tenant_id=tenant_id,
            title=title,
            content=body or title,
            chain="video",
        )
    except Exception:  # noqa: BLE001 — 关卡故障不得阻断视频发布流（零回归）
        logger.warning("video chain gate 异常，视为 off（不改变原流程）")
        return None


def _build_gate_blocked_result(
    gate_report: Any,
    platform_name: str,
) -> dict[str, Any]:
    """构建视频链路关卡拦截结果。"""
    return {
        "success": False,
        "platform_name": platform_name,
        "error_message": "视频链路清洗关拦截：品牌/合规风险",
        "gate_blocked": True,
        "gate": gate_report.to_meta(),
        "attempts": [],
        "via": "gate_blocked",
    }


async def _check_nurture_cycle(
    *,
    nurture_cycle_id: str | None,
    db: Session | None,
    platform_name: str,
    gate_report: Any,
) -> dict[str, Any] | None:
    """养号状态检查，限制发布时返回拦截结果。"""
    if not nurture_cycle_id or not db:
        return None
    from app.services.social_nurture_service import can_publish_now
    check = can_publish_now(db, cycle_id=nurture_cycle_id)
    if check.get("allowed"):
        return None
    result = {
        "success": False,
        "platform_name": platform_name,
        "error_message": f"养号周期限制: {check.get('reason')}",
        "next_available_at": check.get("next_available_at"),
        "nurture_blocked": True,
        "attempts": [],
        "via": "nurture_rate_limit",
    }
    if gate_report is not None and gate_report.verdict != "off":
        result["gate"] = gate_report.to_meta()
    return result


def _build_no_worker_result(
    platform_name: str,
    gate_report: Any,
) -> dict[str, Any]:
    """构建无可用 Worker 的失败结果。"""
    result = {
        "success": False,
        "platform_name": platform_name,
        "error_message": (
            f"{platform_name} 无可用发布 Worker，"
            "请配置 SAU / biliup / xhs-mcp 或 AITOEARN_API_KEY"
        ),
        "attempts": [],
        "via": "blocked",
    }
    if gate_report is not None and gate_report.verdict != "off":
        result["gate"] = gate_report.to_meta()
    return result


async def _prepare_local_video(
    *,
    chain: list[str],
    video_url: str,
    local_video: Path | None,
    platform_name: str,
    gate_report: Any,
) -> tuple[Path | None, Path | None, dict[str, Any] | None]:
    """按需下载远程视频到本地，失败时返回错误结果。"""
    owned_temp: Path | None = None
    video_path = local_video
    needs_local = any(t in chain for t in ("sau", "biliup", "xhs_mcp"))
    if needs_local and video_path is None:
        try:
            video_path = await download_video_to_temp(video_url)
            owned_temp = video_path
        except Exception as exc:
            result = {
                "success": False,
                "platform_name": platform_name,
                "error_message": f"视频拉取失败: {exc}",
                "attempts": [],
                "via": "media_fetch",
            }
            if gate_report is not None and gate_report.verdict != "off":
                result["gate"] = gate_report.to_meta()
            return None, None, result
    return video_path, owned_temp, None


def _record_nurture_post(nurture_cycle_id: str | None, db: Session | None) -> None:
    """发布成功后记录养号操作。"""
    if nurture_cycle_id and db:
        from app.services.social_nurture_service import record_action
        record_action(db, cycle_id=nurture_cycle_id, action_type="post")


def _finalize_result(
    last: dict[str, Any],
    attempts: list[dict[str, Any]],
    gate_report: Any,
    *,
    success: bool,
    failure_message: str | None = None,
) -> dict[str, Any]:
    """整理最终发布结果并附关卡留痕。"""
    last["attempts"] = attempts
    if not success and not last.get("error_message"):
        last["error_message"] = failure_message
    last["success"] = success
    result = annotate_failover_result(last, attempts)
    if gate_report is not None and gate_report.verdict != "off":
        result["gate"] = gate_report.to_meta()
    return result


async def publish_platform_video(
    *,
    platform_name: str,
    video_url: str,
    cover_url: str,
    title: str,
    body: str = "",
    tags: list[str] | None = None,
    tenant_id: str | None = None,
    local_video: Path | None = None,
    allowed_aitoearn_ids: set[str] | None = None,
    scheduled_at: int | None = None,
    nurture_cycle_id: str | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """
    对单个平台按 tier 链尝试，直到验真成功或全部失败。
    返回最后一次尝试的详细结果（含 attempts 轨迹供 Hermes 展示）。

    新增：
    - scheduled_at: 定时发布时间（Unix ms）
    - nurture_cycle_id: 发布前检查养号状态
    - db: 需要时查询养号状态
    """
    # ---- 视频链路双关卡（总纲 §6.4；开关默认关/异常→off，零回归）----
    gate_report = await _check_video_chain_gate(
        tenant_id=tenant_id,
        title=title,
        body=body,
    )
    if gate_report is not None and gate_report.blocked:
        return _build_gate_blocked_result(gate_report, platform_name)

    # 养号状态检查
    nurture_result = await _check_nurture_cycle(
        nurture_cycle_id=nurture_cycle_id,
        db=db,
        platform_name=platform_name,
        gate_report=gate_report,
    )
    if nurture_result is not None:
        return nurture_result

    chain = platform_tier_chain(platform_name)
    if not chain:
        return _build_no_worker_result(platform_name, gate_report)

    video_path, owned_temp, media_error = await _prepare_local_video(
        chain=chain,
        video_url=video_url,
        local_video=local_video,
        platform_name=platform_name,
        gate_report=gate_report,
    )
    if media_error is not None:
        return media_error

    attempts: list[dict[str, Any]] = []
    last: dict[str, Any] = {}
    try:
        for tier in chain:
            try:
                outcome = await _try_tier(
                    tier,
                    platform_name=platform_name,
                    local_video=video_path or Path("_missing_"),
                    title=title,
                    body=body,
                    tags=tags,
                    video_url=video_url,
                    cover_url=cover_url,
                    tenant_id=tenant_id,
                    allowed_aitoearn_ids=allowed_aitoearn_ids,
                    scheduled_at=scheduled_at,
                )
            except Exception as exc:  # noqa: BLE001 — Worker 异常统一记入 attempts（零回归）
                logger.warning("publish tier %s 异常: %s", tier, exc)
                outcome = {
                    "success": False,
                    "platform_name": platform_name,
                    "tier": tier,
                    "via": tier,
                    "error_message": str(exc)[:500],
                }

            attempts.append(
                {
                    "tier": tier,
                    "success": bool(outcome.get("success")),
                    "verified": outcome.get("verified"),
                    "platform_post_url": outcome.get("platform_post_url"),
                    "error_message": outcome.get("error_message"),
                }
            )
            last = outcome
            if outcome.get("success"):
                _record_nurture_post(nurture_cycle_id, db)
                return _finalize_result(
                    last, attempts, gate_report, success=True
                )
    finally:
        if owned_temp and owned_temp.exists():
            try:
                owned_temp.unlink()
            except OSError:
                pass

    return _finalize_result(
        last,
        attempts,
        gate_report,
        success=False,
        failure_message=(
            f"主备双线均已尝试（{len(chain)} 次），均未获得可验证作品链接"
        ),
    )

async def publish_platforms_batch(
    db: Session,
    *,
    platform_names: list[str],
    video_url: str,
    cover_url: str,
    title: str,
    body: str = "",
    tags: list[str] | None = None,
    tenant_id: str | None = None,
    scheduled_at: int | None = None,
    nurture_cycle_ids: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """批量平台发布（共享一次本地下载）。

    新增：
    - scheduled_at: 定时发布时间
    - nurture_cycle_ids: {platform_name: cycle_id} 映射，逐平台检查养号状态
    """
    del db
    chain_any_local = any(
        t in platform_tier_chain(n) for n in platform_names for t in ("sau", "biliup", "xhs_mcp")
    )
    shared: Path | None = None
    if chain_any_local and not scheduled_at:
        shared = await download_video_to_temp(video_url)

    results: list[dict[str, Any]] = []
    try:
        for name in platform_names:
            cycle_id = (nurture_cycle_ids or {}).get(name)
            row = await publish_platform_video(
                platform_name=name,
                video_url=video_url,
                cover_url=cover_url,
                title=title,
                body=body,
                tags=tags,
                tenant_id=tenant_id,
                local_video=shared,
                scheduled_at=scheduled_at,
                nurture_cycle_id=cycle_id,
                db=db,
            )
            results.append(row)
    finally:
        if shared and shared.exists():
            try:
                shared.unlink()
            except OSError:
                pass
    return results
