# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""ContentAsset 服务 —— 既有内容的统一收敛层（修正设计稿 模块4 / 契约 §4）。

核心裁定（契约 §4）：ContentAsset 不是新表，而是既有表的**读模型 / facade**：
`ContentMaster`（+ `fact_kernel_json`）+ `Tenant` + 模块2 `IndustryProfile` +
`PublishTask` + `InclusionStatus` + `MarketingTouchpoint` 聚合为一个 DTO。

三条硬约束：
1. **租户隔离**：只读 `content_masters`（有 tenant_id）。严禁读 `content_pages` /
   `content_versions`（实测无 tenant_id，会把全局静态页当租户资产 → 跨租户泄露）。
2. **FAIL-SAFE 铁律**：任一环节取不到数据（kernel 为 NULL / 表缺行 / 关联断 /
   JSON 非法）→ **降级不抛异常**；kernel 空时回落 `draft`。
3. **canonical 收口**：唯一真源优先级 = `tenant_canonical_url` → 租户主域 + route →
   `settings.SITE_URL`；**禁止**产出平台默认域（建材站 / 国际化站硬编码默认域，
   本模块不触碰那批旧硬编码，仅保证新路径不落入平台默认域）。
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.attribution import MarketingTouchpoint
from app.models.content import InclusionStatus, PublishTask
from app.models.content_master import ContentMaster
from app.models.tenant import Tenant
from app.schemas.content_asset import ContentAssetOut
from app.services import industry_profile_service, tenant_domain_service

logger = logging.getLogger(__name__)

# publish_tasks.status 视为「发布成功」的取值集合。
# 契约 §4.1 口径为 'success'；'published' 为现网历史漂移值（实查 publish_tasks 存在），
# 一并容忍，避免把已发布的内容误判为 queued。
_PUBLISH_SUCCESS_STATES = frozenset({"success", "published"})

# language 缺省（契约 §4：租户默认语）
_DEFAULT_LANGUAGE = "zh"

# canonical route 约定（**暂定**）——现有源码无租户内容 canonical 路径先例，
# 最近约定为 api/v1/sitemap.py:169 的 `{base}/content/{slug}` 与 `/{locale}` 前缀。
# 取 `/{language}/content/{master.id}`；待模块20 前端 / 模块1 域名收口确认后收敛。
_CANONICAL_ROUTE_TMPL = "/{language}/content/{asset_id}"


# ────────────────────────────── canonical ──────────────────────────────


def _primary_host(db: Session, tenant_id: Any) -> Optional[str]:
    """租户主域 host：筛 is_primary + is_active + verification_status=='verified'。"""
    if not tenant_id:
        return None
    try:
        domains = tenant_domain_service.list_for_tenant(db, str(tenant_id))
    except Exception as exc:  # noqa: BLE001 —— 取域失败不得阻断 facade
        logger.warning("读取租户 %s 域名失败，canonical 回落：%s", tenant_id, exc)
        return None
    for d in domains:
        if (
            getattr(d, "is_primary", False) is True
            and getattr(d, "is_active", False) is True
            and (getattr(d, "verification_status", "") or "") == "verified"
        ):
            host = (getattr(d, "normalized_hostname", "") or getattr(d, "hostname", "") or "").strip()
            if host:
                return host
    return None


def build_canonical_url(
    db: Session,
    tenant: Optional[Tenant],
    master: ContentMaster,
    language: Optional[str] = None,
) -> str:
    """统一产出内容 canonical_url（契约 §4.2 冻结优先级）。

    ① `master.tenant_canonical_url` 非空即用；
    ② 否则 = `https://{租户主域}` + route；
    ③ 否则回落 `settings.SITE_URL` + route。
    """
    explicit = getattr(master, "tenant_canonical_url", None)
    if explicit and str(explicit).strip():
        return str(explicit).strip()

    lang = (language or _DEFAULT_LANGUAGE).strip() or _DEFAULT_LANGUAGE
    route = _CANONICAL_ROUTE_TMPL.format(language=lang, asset_id=master.id)

    host = _primary_host(db, getattr(tenant, "id", None)) if tenant is not None else None
    if host:
        return f"https://{host}{route}"

    base = (getattr(settings, "SITE_URL", "") or "").rstrip("/")
    return f"{base}{route}"


# ────────────────────────────── 状态机派生 ──────────────────────────────


def _tasks_for_master(db: Session, master: ContentMaster) -> list[PublishTask]:
    """该母版关联的发布任务（按 content_master_id；1 Content → N Task）。"""
    return (
        db.query(PublishTask)
        .filter(PublishTask.content_master_id == master.id)
        .all()
    )


def _kernel_schema_ready(master: ContentMaster) -> bool:
    """`fact_kernel_json.schema_ready == true`（缺失/非 dict/非 True → False，不抛）。"""
    kernel = getattr(master, "fact_kernel_json", None)
    if not isinstance(kernel, dict):
        return False
    return kernel.get("schema_ready") is True


def _inclusion_failed(db: Session, success_tasks: list[PublishTask]) -> bool:
    """有发布成功任务但收录校验失败：inclusion_status.is_included=false。

    `inclusion_status.task_id` 实测 FK → `publish_tasks.id`（models/content.py:287），
    语义成立 → `verification_failed` 可达。取数失败一律 False（不误判）。
    """
    task_ids = [t.id for t in success_tasks if getattr(t, "id", None) is not None]
    if not task_ids:
        return False
    try:
        rows = (
            db.query(InclusionStatus)
            .filter(InclusionStatus.task_id.in_(task_ids))
            .all()
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 inclusion_status 失败，verification_failed 判定跳过：%s", exc)
        return False
    return any(getattr(r, "is_included", None) is False for r in rows)


def derive_content_status(db: Session, master: ContentMaster) -> str:
    """按契约 §4.1 优先级派生 content_status（命中即停，全程 fail-safe）。"""
    try:
        # archived：deleted_at 非空 或 status 显式 archived
        if getattr(master, "deleted_at", None) is not None:
            return "archived"
        if (getattr(master, "status", "") or "").strip().lower() == "archived":
            return "archived"

        tasks = _tasks_for_master(db, master)
        success_tasks = [
            t for t in tasks
            if (getattr(t, "status", "") or "").strip().lower() in _PUBLISH_SUCCESS_STATES
        ]
        if success_tasks:
            if _inclusion_failed(db, success_tasks):
                return "verification_failed"
            return "published"
        if tasks:
            return "queued"
        if getattr(master, "preflight_approved_at", None) is not None:
            return "approved"
        if _kernel_schema_ready(master):
            return "fact_checked"
        return "draft"
    except Exception as exc:  # noqa: BLE001 —— 任一环节异常 → 降级 draft，绝不外抛
        logger.warning("派生 content_status 失败，回落 draft：%s", exc)
        return "draft"


def derive_publish_status(db: Session, master: ContentMaster) -> str:
    """按 `publish_tasks`（content_master_id）聚合发布状态；无任务 = 'unpublished'。"""
    try:
        tasks = _tasks_for_master(db, master)
    except Exception as exc:  # noqa: BLE001
        logger.warning("派生 publish_status 失败，回落 unpublished：%s", exc)
        return "unpublished"
    if not tasks:
        return "unpublished"
    states = [(getattr(t, "status", "") or "").strip().lower() for t in tasks]
    if any(s in _PUBLISH_SUCCESS_STATES for s in states):
        return "published"
    if all(s == "failed" for s in states):
        return "failed"
    if any(s == "processing" for s in states):
        return "processing"
    return "pending"


def derive_attribution_context(db: Session, master: ContentMaster) -> dict[str, Any]:
    """归因上下文：`marketing_touchpoints where tenant_id=… and content_id=str(master.id)`。

    约定（契约 §6.2 冻结）：`content_id = str(master.id)`。无触点 → `{}`。
    """
    try:
        rows = (
            db.query(MarketingTouchpoint)
            .filter(
                MarketingTouchpoint.tenant_id == master.tenant_id,
                MarketingTouchpoint.content_id == str(master.id),
            )
            .all()
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("派生 attribution_context 失败，回落空：%s", exc)
        return {}
    if not rows:
        return {}
    platforms = sorted(
        {(getattr(r, "platform", "") or "").strip() for r in rows if (getattr(r, "platform", "") or "").strip()}
    )
    occurred = [getattr(r, "occurred_at", None) for r in rows if getattr(r, "occurred_at", None) is not None]
    ctx: dict[str, Any] = {
        "touches": len(rows),
        "platforms": platforms,
        "content_id": str(master.id),
    }
    if occurred:
        ctx["last_touch_at"] = max(occurred).isoformat()
    return ctx


# ────────────────────────────── 组装 ──────────────────────────────


def _as_list(value: Any) -> list[Any]:
    """asset_meta 中 list 字段：非 list / 缺失 → []（诚实降级）。"""
    return value if isinstance(value, list) else []


def _asset_meta(master: ContentMaster) -> dict[str, Any]:
    meta = getattr(master, "asset_meta", None)
    return meta if isinstance(meta, dict) else {}


def build_content_asset(db: Session, master: ContentMaster) -> ContentAssetOut:
    """把一条 `ContentMaster` 聚合为 ContentAssetOut（15 字段）。

    只读 `content_masters`（+ 其 tenant_id 作用域内的派生数据），绝不触碰
    `content_pages` / `content_versions`。
    """
    tenant: Optional[Tenant] = None
    try:
        tenant = db.query(Tenant).filter(Tenant.id == master.tenant_id).first()
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取租户 %s 失败，site_id 回落 None：%s", master.tenant_id, exc)

    profile = None
    try:
        profile = industry_profile_service.resolve_profile_for_tenant(db, master.tenant_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("解析租户 %s 行业包失败，industry_profile_id 回落 None：%s", master.tenant_id, exc)

    meta = _asset_meta(master)
    language = meta.get("language") or _DEFAULT_LANGUAGE

    kernel = getattr(master, "fact_kernel_json", None)
    evidence_refs: list[Any] = []
    if isinstance(kernel, dict):
        evidence_refs = _as_list(kernel.get("evidence"))

    return ContentAssetOut(
        asset_id=str(master.id),
        tenant_id=str(master.tenant_id),
        site_id=(getattr(tenant, "domain", None) if tenant is not None else None),
        industry_profile_id=(str(profile.id) if profile is not None else None),
        product_id=meta.get("product_id"),
        market=meta.get("market"),
        language=language,
        source_refs=_as_list(meta.get("source_refs")),
        evidence_refs=evidence_refs,
        prompt_version=meta.get("prompt_version"),
        model_version=meta.get("model_version"),
        content_status=derive_content_status(db, master),
        publish_status=derive_publish_status(db, master),
        canonical_url=build_canonical_url(db, tenant, master, language),
        attribution_context=derive_attribution_context(db, master),
    )


__all__ = [
    "build_canonical_url",
    "derive_content_status",
    "derive_publish_status",
    "derive_attribution_context",
    "build_content_asset",
]
