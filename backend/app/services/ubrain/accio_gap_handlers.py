"""Accio 对标 gap 技能 — 预览载荷 + 带 DB 上下文真执行。"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.services.ubrain.accio_gap_constants import GAP_EXECUTE_SKILL_IDS, GAP_MVP_SKILL_IDS
from app.services.ubrain.accio_skill_catalog import get_skill
from app.services.ubrain.matrix_publish_service import (
    build_matrix_publish_plan,
    default_platform_names,
    execute_matrix_publish,
    resolve_platform_ids,
)
from app.services.ubrain.team_rbac_service import build_team_rbac_snapshot


def is_gap_mvp_skill(skill_id: str) -> bool:
    """is_gap_mvp_skill。

    参数说明：
    :param skill_id: 参数 skill_id
    :return: 返回处理结果。
    """
    return skill_id in GAP_MVP_SKILL_IDS


def is_gap_execute_skill(skill_id: str) -> bool:
    """is_gap_execute_skill。

    参数说明：
    :param skill_id: 参数 skill_id
    :return: 返回处理结果。
    """
    return skill_id in GAP_EXECUTE_SKILL_IDS


def execute_gap_mvp(
    skill_id: str,
    *,
    image_url: Optional[str] = None,
    keywords: Optional[str] = None,
    product_hint: Optional[str] = None,
    locale: str = "zh",
    budget_usd: Optional[float] = None,
    rfq_lines: Optional[str] = None,
    db: Session | None = None,
    tenant_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> Optional[dict[str, Any]]:
    """GET /gap 预览载荷；仅 partial MVP 技能或 execute 技能预览。"""
    if skill_id not in GAP_EXECUTE_SKILL_IDS:
        return None
    sk = get_skill(skill_id) or {}
    base: dict[str, Any] = {
        "skill_id": skill_id,
        "accio_analog": sk.get("accio_analog"),
        "implemented": sk.get("implemented"),
        "mvp": skill_id in GAP_MVP_SKILL_IDS,
        "north_star": "bytedance_deerflow_research + alibaba_accio_execution",
    }
    ctx = dict(context or {})
    if skill_id == "image_sourcing":
        base.update(_mvp_image_sourcing(image_url=image_url, keywords=keywords))
    elif skill_id == "auto_shopify":
        base.update(_mvp_auto_shopify(product_hint=product_hint, locale=locale))
    elif skill_id == "paid_ads_creative":
        base["execute_api"] = "POST /api/v1/ubrain/commercial-os/gap/paid_ads_creative/execute"
        base.update(_mvp_paid_ads_sync(product_hint=product_hint, budget_usd=budget_usd))
    elif skill_id == "supplier_rfq":
        base.update(_mvp_supplier_rfq(rfq_lines=rfq_lines, product_hint=product_hint))
    elif skill_id == "matrix_publish":
        base.update(
            _mvp_matrix_publish(
                product_hint=product_hint,
                locale=locale,
                db=db,
                tenant_id=tenant_id,
                context=ctx,
            )
        )
    elif skill_id == "team_rbac":
        base.update(_mvp_team_rbac(db=db))
    return base


async def execute_gap_mvp_async(
    skill_id: str,
    *,
    db: Session,
    tenant_id: str,
    product_hint: Optional[str] = None,
    locale: str = "zh",
    budget_usd: Optional[float] = None,
    context: dict[str, Any] | None = None,
    message: str = "",
    user_id: str | None = None,
) -> Optional[dict[str, Any]]:
    """POST /gap/{id}/execute — 矩阵发布、建站、广告创意等。"""
    ctx = dict(context or {})
    if skill_id == "matrix_publish":
        return execute_matrix_publish(
            db,
            tenant_id=tenant_id,
            message=message or "矩阵发布",
            context=ctx,
            user_id=user_id,
        )
    if skill_id == "paid_ads_creative":
        from app.services.ubrain.paid_ads_creative_service import generate_paid_ads_creative
        payload = await generate_paid_ads_creative(
            db,
            tenant_id=tenant_id,
            product_hint=product_hint or "insulation export",
            budget_usd=budget_usd or 500.0,
            locale=locale,
        )
        sk = get_skill(skill_id) or {}
        payload.update(
            {
                "skill_id": skill_id,
                "accio_analog": sk.get("accio_analog"),
            }
        )
        return payload
    if skill_id == "auto_shopify":
        from app.models.tenant import Tenant
        from app.services.hermes.site_build_workflow import run_ai_site_builder_v1
        from app.services.tenant_site_persistence import persist_tenant_site_content
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"status": "failed", "error": "tenant_not_found"}
        product = (product_hint or "保温建材").strip()
        result = await run_ai_site_builder_v1(
            db,
            tenant_id=tenant_id,
            product_name=product,
            company_name=tenant.name or "",
            auto_save=True,
            use_ai=bool(ctx.get("use_ai", True)),
            persist_fn=persist_tenant_site_content,
        )
        return {
            "status": "success",
            "mode": "tenant_independent_domain",
            "site_content": result.get("site_content"),
            "saved": bool(result.get("saved")),
            "source": result.get("source"),
            "client_path": "/client/site-editor",
            "api": "POST /api/v1/tenants/self/site-generate",
        }
    if skill_id == "team_rbac":
        return _mvp_team_rbac(db=db)
    return execute_gap_mvp(
        skill_id,
        product_hint=product_hint,
        locale=locale,
        budget_usd=budget_usd,
        db=db,
        tenant_id=tenant_id,
        context=ctx,
    )


def _mvp_image_sourcing(*, image_url: Optional[str], keywords: Optional[str]) -> dict[str, Any]:
    """_mvp_image_sourcing。

    参数说明：
    :param image_url: 参数 image_url
    :param keywords: 参数 keywords
    :return: 返回处理结果。
    """
    kw = (keywords or "").strip() or "insulation board"
    return {
        "mode": "keyword_heuristic",
        "input": {"image_url": image_url, "keywords": kw},
        "matches": [
            {
                "title": f"建材候选 · {kw}",
                "category": "building_materials",
                "confidence": 0.72 if image_url else 0.58,
                "source": "catalog_heuristic",
                "next_step": "POST /api/v1/ubrain/chat intent=find_buyers",
            },
        ],
        "note": "完整以图搜品需图搜/1688 合作；当前为关键词启发式 MVP",
    }


def _mvp_auto_shopify(*, product_hint: Optional[str], locale: str) -> dict[str, Any]:
    """_mvp_auto_shopify。

    参数说明：
    :param product_hint: 参数 product_hint
    :param locale: 参数 locale
    :return: 返回处理结果。
    """
    hint = (product_hint or "default").strip()
    return {
        "mode": "tenant_independent_domain",
        "site_blueprint": {
            "template": "b2b_insulation_export",
            "locale": locale,
            "product_focus": hint,
            "estimated_minutes": 45,
        },
        "execute_api": "POST /api/v1/ubrain/commercial-os/gap/auto_shopify/execute",
        "api_action": {
            "method": "POST",
            "path": "/api/v1/tenants/self/site-generate",
            "body": {"product_name": hint, "auto_save": True},
        },
        "use_instead": "/client/site-editor",
        "note": "独立域+B2B 模板替代 Shopify；execute 端点可一键生成并落库",
    }


def _mvp_paid_ads_sync(*, product_hint: Optional[str], budget_usd: Optional[float]) -> dict[str, Any]:
    """_mvp_paid_ads_sync。

    参数说明：
    :param product_hint: 参数 product_hint
    :param budget_usd: 参数 budget_usd
    :return: 返回处理结果。
    """
    product = (product_hint or "insulation export").strip()
    budget = budget_usd if budget_usd is not None else 500.0
    return {
        "mode": "creative_pack_draft",
        "budget_usd": budget,
        "variants": [
            {
                "channel": "google_search",
                "headline": f"Export-grade {product[:40]}",
                "description": "Factory direct · MOQ flexible · CE/ISO",
            },
        ],
        "next_step": "POST /api/v1/ubrain/commercial-os/gap/paid_ads_creative/execute",
    }


def _mvp_supplier_rfq(*, rfq_lines: Optional[str], product_hint: Optional[str]) -> dict[str, Any]:
    """_mvp_supplier_rfq。

    参数说明：
    :param rfq_lines: 参数 rfq_lines
    :param product_hint: 参数 product_hint
    :return: 返回处理结果。
    """
    lines = [ln.strip() for ln in (rfq_lines or "").splitlines() if ln.strip()] or [
        "MOQ 500",
        "FOB Shanghai",
    ]
    return {
        "mode": "rfq_compare_stub",
        "product": (product_hint or "general").strip(),
        "lines": lines,
        "suppliers": [
            {"name": "Supplier A (demo)", "unit_price_usd": 12.5, "score": 0.81},
        ],
        "use_instead": "/client/copilot",
    }


def _mvp_matrix_publish(
    *,
    product_hint: Optional[str],
    locale: str,
    db: Session | None = None,
    tenant_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """_mvp_matrix_publish。

    参数说明：
    :param product_hint: 参数 product_hint
    :param locale: 参数 locale
    :param db: 参数 db
    :param tenant_id: 参数 tenant_id
    :param context: 参数 context
    :return: 返回处理结果。
    """
    ctx = dict(context or {})
    hint = (product_hint or ctx.get("content_source") or "content_master").strip()
    platforms = ctx.get("platforms") or default_platform_names(locale=locale)
    plan = build_matrix_publish_plan({**ctx, "platforms": platforms, "content_source": hint})
    payload: dict[str, Any] = {
        "mode": "publish_plan",
        "platforms": plan["platforms"],
        "content_source": hint,
        "cta": plan["cta"],
        "human_confirmation_required": True,
        "execute_api": "POST /api/v1/ubrain/commercial-os/gap/matrix_publish/execute",
        "use_instead": "/client/publish",
    }
    if db is not None:
        from app.services.publish_workers.tier_router import preflight_workers
        payload["preflight"] = preflight_workers()
        _, bindings = resolve_platform_ids(db, plan["platforms"], tenant_id=tenant_id)
        payload["platform_bindings"] = bindings
    return payload


def _mvp_team_rbac(*, db: Session | None = None) -> dict[str, Any]:
    """_mvp_team_rbac。

    参数说明：
    :param db: 参数 db
    :return: 返回处理结果。
    """
    snap = build_team_rbac_snapshot(db)
    return {**snap, "use_instead": "/admin/users"}
