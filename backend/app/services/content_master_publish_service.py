# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""统一发布母版 — 按平台名匹配变体并创建 PublishTask。

双关卡接入（总纲 §6.4，文章链路）：
- 特性开关 `PIPELINE_GATES_ENABLED=1` 启用（默认关，零回归）；
- 清洗关硬拦截（品牌/广告法违规）：跳过建任务，matches 记 reason=gate_blocked；
- 复核关为标记语义：发布任务附带 gate 元数据（人审标记由执行侧处置）。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Platform, PlatformAccount, PublishTask
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.services.hub_urls import build_dual_links
from app.services.foreign_trade.utm_attribution_service import (
    build_default_publish_utm,
    stamp_publish_task_utm,
)

logger = logging.getLogger(__name__)


class _NullGateReport:
    """关卡不可用/开关关闭时的空裁决（不改变原流程，零回归红线）。"""
    blocked = False
    review_required = False
    def to_meta(self) -> dict[str, Any]:
        """to_meta。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {"verdict": "off", "review_required": False, "issues": [], "score": None}


def _gate_master_content(db: Session, tenant_id: str, master: ContentMaster) -> Any:
    """文章链路双关卡评估（总纲 §6.4）。模块不可用/开关关 → off。"""
    try:
        from app.services.pipeline.chains import gate_content  # noqa: PLC0415
    except Exception:  # noqa: BLE001 — 关卡模块不可用不得阻断发布流
        logger.warning("pipeline chains 不可用，文章关卡跳过")
        return _NullGateReport()
    content = (
        getattr(master, "body", None)
        or getattr(master, "content", None)
        or getattr(master, "summary", None)
        or ""
    )
    return gate_content(
        db,
        tenant_id=tenant_id,
        title=master.title or "",
        content=content,
        chain="article",
    )


def _pick_master_for_platform(
    drafts: list[ContentMaster],
    platform_name: str,
    *,
    fallback: ContentMaster | None,
) -> ContentMaster | None:
    """_pick_master_for_platform。

    参数说明：
    :param drafts: 参数 drafts
    :param platform_name: 参数 platform_name
    :param fallback: 参数 fallback
    :return: 返回处理结果。
    """
    name = (platform_name or "").strip()
    prefix = f"[{name}]"
    for row in drafts:
        if (row.title or "").startswith(prefix):
            return row
    short = name.split("(")[0].split("（")[0].strip()
    if short and short != name:
        alt_prefix = f"[{short}]"
        for row in drafts:
            if (row.title or "").startswith(alt_prefix):
                return row
    for row in drafts:
        title = row.title or ""
        if name and name in title:
            return row
        if short and short in title:
            return row
    return fallback


def _publish_single_platform(
    db: Session,
    tenant,
    tenant_id: str,
    plat,
    drafts: list,
    fallback,
    gate_cache: dict[str, Any],
    utm: dict[str, str] | None,
    utm_campaign: str | None,
    primary_url: str | None,
    secondary_url: str | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """处理单个平台的发布任务创建，返回 (match 记录, task_id)。无匹配时 match 为 None。"""
    account = (
        db.query(PlatformAccount)
        .filter(
            PlatformAccount.platform_id == plat.id,
            PlatformAccount.tenant_id == tenant_id,
            PlatformAccount.is_active.is_(True),
        )
        .first()
    )
    if not account:
        return (
            {
                "platform_id": plat.id,
                "platform_name": plat.name,
                "skipped": True,
                "reason": "no_account",
            },
            None,
        )

    master = _pick_master_for_platform(drafts, plat.name or "", fallback=fallback)
    if not master:
        return None, None

    # ---- 双关卡（总纲 §6.4；开关默认关，零回归）----
    gate_report = gate_cache.get(master.id)
    if gate_report is None:
        gate_report = _gate_master_content(db, tenant_id, master)
        gate_cache[master.id] = gate_report
    if gate_report.blocked:
        return (
            {
                "platform_id": plat.id,
                "platform_name": plat.name,
                "content_master_id": master.id,
                "skipped": True,
                "reason": "gate_blocked",
                "gate": gate_report.to_meta(),
            },
            None,
        )

    plat_code = (plat.name or "platform")[:32].replace(" ", "_")
    auto_primary, auto_secondary = build_dual_links(tenant, master, plat_code)
    task = PublishTask(
        content_master_id=master.id,
        platform_id=plat.id,
        account_id=account.id,
        region=getattr(plat, "region", None) or "cn",
        primary_url=primary_url or auto_primary,
        secondary_url=secondary_url if secondary_url is not None else auto_secondary,
        status="pending",
    )
    stamp_publish_task_utm(
        task,
        utm=utm
        or build_default_publish_utm(
            platform_name=plat.name or "",
            campaign=utm_campaign,
            content_master_id=str(master.id),
        ),
        tenant_id=tenant_id,
    )
    db.add(task)
    db.flush()
    master.status = "ready"
    # 一核多形（缺口 #8 持久化）：变体/DeerFlow 发布路径同样落一份事实内核快照，
    # 使同一母版的多平台形态都源自同一份可回溯的硬事实，而非每次现算即丢。
    try:
        from app.services.geo.content_kernel_bridge import persist_kernel

        persist_kernel(master)
    except Exception as exc:  # 内核落库失败不得阻断发布主链
        logger.debug("事实内核快照落库失败 master=%s: %s", master.id, exc)
    match = {
        "platform_id": plat.id,
        "platform_name": plat.name,
        "content_master_id": master.id,
        "content_title": master.title,
        "task_id": task.id,
        "gate": gate_report.to_meta(),
        "login_status": account.login_status or "logged_out",
        "bind_warning": (
            "platform_not_bound"
            if (account.login_status or "") != "logged_in"
            else None
        ),
    }
    return match, task.id


def publish_auto_variants(
    db: Session,
    *,
    tenant_id: str,
    platform_ids: list[str],
    draft_ids: list[str] | None = None,
    fallback_master_id: str | None = None,
    primary_url: str | None = None,
    secondary_url: str | None = None,
    utm: dict[str, str] | None = None,
    utm_campaign: str | None = None,
) -> dict[str, Any]:
    """
    为每个 platform_id 创建发布任务：
    - 优先匹配 title 以 [平台名] 开头的变体草稿
    - 否则使用 fallback_master_id 或第一篇母版草稿
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError("tenant_not_found")

    q = db.query(ContentMaster).filter(
        ContentMaster.tenant_id == tenant_id,
        ContentMaster.status.in_(("draft", "ready")),
    )
    if draft_ids:
        q = q.filter(ContentMaster.id.in_(draft_ids))
    drafts = q.order_by(ContentMaster.created_at.desc()).limit(50).all()
    if not drafts:
        raise ValueError("no_drafts")

    fallback: ContentMaster | None = None
    if fallback_master_id:
        fallback = next((d for d in drafts if d.id == fallback_master_id), None)
    if fallback is None:
        fallback = next(
            (d for d in drafts if not (d.title or "").startswith("[GEO清单]")),
            drafts[0],
        )

    platforms = (
        db.query(Platform)
        .filter(Platform.id.in_(platform_ids), Platform.is_active)
        .all()
    )
    if not platforms:
        raise ValueError("no_platforms")

    task_ids: list[str] = []
    matches: list[dict[str, Any]] = []
    gate_cache: dict[str, Any] = {}  # 同一母版多平台只评估一次关卡
    for plat in platforms:
        match, task_id = _publish_single_platform(
            db, tenant, tenant_id, plat, drafts, fallback, gate_cache,
            utm, utm_campaign, primary_url, secondary_url,
        )
        if match is not None:
            matches.append(match)
        if task_id is not None:
            task_ids.append(task_id)

    if not task_ids:
        raise ValueError("no_tasks_created")

    db.commit()
    return {
        "task_ids": task_ids,
        "count": len(task_ids),
        "matches": matches,
    }
