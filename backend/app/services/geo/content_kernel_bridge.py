# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""内核接线层 — 把「母版 + 产品快照」落成事实内核，供发布台/Worker 按形态投影。

对应缺口 #8（接线）：unified_publish 发布任务执行前调用
`build_kernel_from_master`，得到 FactKernel 后走
`platform_content_router.route(group, region, platform)` 出各平台形态，
替代「同一篇长文端给 40 家」。

设计铁律（AGENTS.md §4 交付求真）：
- 内核降级时返回 degraded 内核，路由输出如实带 incomplete，不假成功。
- 组装（build/project）不写 DB、不发网络；持久化只改 ORM 属性，提交由调用方负责。
- `persist_kernel` 只在真组出内核时落库：组不出（无标题）就返回 None，绝不写假快照。
- `load_or_build` 优先复用母版已落库内核（一核多形的「核」必须稳定），
  仅当快照缺失或调用方给了更新的产品硬事实时才重组。
"""

from __future__ import annotations

from typing import Any, Optional

from app.models.content_master import ContentMaster
from app.services.geo.content_kernel import FactKernel
from app.services.geo.platform_content_router import route as _route

# 参与内核事实层的母版字段：变了就得重组，否则会用旧快照发新文案
_FACT_FIELDS = ("title", "body", "media_urls", "tenant_canonical_url", "tenant_id")


def build_kernel_from_master(
    master: ContentMaster,
    product_snapshot: Optional[dict[str, Any]] = None,
) -> FactKernel:
    """由母版 + 产品快照组装一份事实内核。

    优先级：product_snapshot（结构化硬事实）> 母版文案（事实层）。
    母版只给 title/body/media_urls，硬事实（MOQ/交期/认证）来自产品快照；
    快照缺失时退化为纯文案内核并如实标记 degraded。
    """
    snap = dict(product_snapshot or {})
    # 产品快照里的规格/贸易条款优先，母版文案作为事实层兜底
    raw: dict[str, Any] = {
        "entity_name": master.title,
        "entity_type": snap.get("entity_type", "product"),
        "entity_aliases": snap.get("entity_aliases") or snap.get("aliases") or [],
        "attrs": {
            "description": master.body or snap.get("description"),
            "image_url": (master.media_urls or [None])[0]
            if master.media_urls
            else snap.get("image_url"),
            **{k: v for k, v in snap.items() if k not in ("entity_type", "aliases", "entity_aliases", "trade", "evidence", "copy", "description", "image_url", "entity_name", "name")},
        },
        "trade": snap.get("trade") or {},
        "evidence": snap.get("evidence") or [],
        "copy": snap.get("copy") or {},
        "source_url": master.tenant_canonical_url or snap.get("source_url") or "",
        "source_tenant": str(master.tenant_id),
    }
    return FactKernel.from_dict(raw)


def kernel_from_master(
    master: ContentMaster,
    product_snapshot: Optional[dict[str, Any]] = None,
) -> Optional[FactKernel]:
    """取母版的「那一个核」：已落库快照优先，其次现组，组不出返回 None。

    给了 product_snapshot（新硬事实）时强制重组，不被旧快照锁死。
    """
    cached = getattr(master, "fact_kernel_json", None)
    if isinstance(cached, dict) and cached and not product_snapshot:
        return FactKernel.from_dict(cached)
    if not (master.title or "").strip():
        return None
    return build_kernel_from_master(master, product_snapshot)


def persist_kernel(
    master: ContentMaster,
    product_snapshot: Optional[dict[str, Any]] = None,
) -> Optional[FactKernel]:
    """把事实内核落到 master.fact_kernel_json（不 commit，调用方管事务）。

    降级内核如实落库（to_dict 自带 schema_ready / completeness），
    让下游与运维看得见「这条内容当时缺哪些硬事实」。
    """
    kernel = kernel_from_master(master, product_snapshot)
    if kernel is None:
        return None
    master.fact_kernel_json = kernel.to_dict()
    return kernel


def invalidate_kernel(master: ContentMaster) -> None:
    """母版事实字段被改写后作废旧快照，下次取用时按新文案重组。"""
    if getattr(master, "fact_kernel_json", None):
        master.fact_kernel_json = None


def touch_kernel_on_update(master: ContentMaster, changed: set[str]) -> None:
    """ORM 事件助手：只在内核相关字段真变了时作废快照。"""
    if changed & set(_FACT_FIELDS):
        invalidate_kernel(master)


def project_for_platform(
    master: ContentMaster,
    product_snapshot: Optional[dict[str, Any]],
    platform_name: str,
    group: str,
    region: str = "cn",
) -> dict[str, Any]:
    """一核多形：组装内核后，按目标平台形态组投影。

    返回路由输出 dict；degraded 内核会带 incomplete 标记，发布侧据此降级。
    """
    kernel = kernel_from_master(master, product_snapshot) or build_kernel_from_master(
        master, product_snapshot
    )
    platform_kw = "alibaba_offer" if "ali" in platform_name.lower() else "generic"
    return _route(
        kernel,
        group,
        region=region,
        platform=platform_kw,
    )


__all__ = [
    "build_kernel_from_master",
    "kernel_from_master",
    "persist_kernel",
    "invalidate_kernel",
    "touch_kernel_on_update",
    "project_for_platform",
]
