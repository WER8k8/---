# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""公开 API — 租户官网的「采购 Agent 可撮合出口」（对标阿里国际 Accio Work / Shopify UCP）。

为什么需要这一层（2026-09-14 竞品雷达结论）：
    买家侧正在把 AI agent 当采购入口（Accio Work 找供应商与比价；Shopify 把 Meta
    做成后台里的 "AI 渠道"，并与 Google 共建 UCP）。优丁的商业闭环假设是
    "内容分发出去 → 流量回租户官网 → 询盘"。如果官网只有 llms.txt + JSON-LD，
    agent 能**读懂**但**接不上**：既不能按需求筛货，也不能直接把询盘递进来。
    本模块补的就是"接得上"那一半。

设计边界（重要）：
    1. **不开侧门**：询盘一律走 `create_public_lead`，与租户官网表单同一条管线
       （自动发现追问、通知分配、GoodJob 池投影、归因），只是额外打 agent 来源标记。
    2. **不编造事实**：目录只透出数据库里真实存在的字段；没有的（价格、MOQ、认证）
       一律显式写 `disclosed: false`，而不是给个看起来合理的默认值。
       报价与合规承诺必须回到人工，`transactionable: false` 明确声明本端点不下单。
    3. **租户隔离**：所有读取按 domain 解析出的 tenant 过滤，绝不跨租户出品。
    4. 公开写入口自带限流与去重（对齐 rfq.py 的既有做法）。
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.cache import get_cache, redis_client, set_cache
from app.core.response import error_response, success_response
from app.db.session import get_db
from app.models.product import Product
from app.services.matching_engine.engine import MatchingEngine
from app.services.matching_engine.schemas import ProductMatchRequest
from app.services.media_tenant_traffic_service import get_tenant_by_domain

logger = logging.getLogger("uj-admin.public_agent_storefront")

# FIX-30 自动注入：与 public_tenant_geo 等公开租户端点同一前缀族
ROUTE_PREFIX = "/public"

router = APIRouter(tags=["公开-租户Agent出口"])

# 对外声明的协议版本：字段语义变更时必须递增，agent 侧据此判断兼容性。
PROTOCOL_VERSION = "youding-agent-storefront/1.0"

_AGENT_INQUIRY_RATE_LIMIT = 5
_AGENT_INQUIRY_RATE_WINDOW = 600  # 秒
_CATALOG_MAX = 50


class AgentInquiryCreate(BaseModel):
    """采购 agent 提交的询盘。

    `agent_name` / `agent_operator` 必填：要让人看得出这条询盘是机器代发的、
    代表谁发的，业务员才知道该怎么接。
    """

    name: str = Field(..., min_length=1, max_length=100, description="终端买方联系人或公司名")
    message: str = Field(..., min_length=10, max_length=4000, description="采购需求原文")
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    product: Optional[str] = Field(None, max_length=200, description="意向品类或产品名")
    product_slugs: list[str] = Field(default_factory=list, max_length=20)
    quantity: Optional[str] = Field(None, max_length=100, description="需求量（原样透传，不做换算）")
    destination_country: Optional[str] = Field(None, max_length=80)
    agent_name: str = Field(..., min_length=1, max_length=120, description="发起本次询盘的 agent 产品名")
    agent_operator: str = Field(..., min_length=1, max_length=200, description="agent 运营方（公司/组织）")
    agent_url: Optional[str] = Field(None, max_length=500, description="agent 侧可回话的地址")
    idempotency_key: Optional[str] = Field(
        None, max_length=120, description="同一 key 在窗口期内只落一条，供 agent 安全重试"
    )
    model_config = {"extra": "ignore"}


def _client_ip(request: Request) -> str:
    """取客户端 IP（与本仓其他公开端点一致，优先 X-Forwarded-For 首段）。"""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_agent_inquiry_rate(ip: str) -> None:
    """公开写入口限流：Redis 原子计数，Redis 不可用时退进程内窗口。"""
    key = f"agent_inquiry:rate:{ip}"
    if redis_client:
        try:
            current = redis_client.incr(key)
            if current == 1:
                redis_client.expire(key, _AGENT_INQUIRY_RATE_WINDOW)
            if current > _AGENT_INQUIRY_RATE_LIMIT:
                raise HTTPException(429, "该来源提交过于频繁，请稍后再试")
            return
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("agent 询盘限流查 Redis 失败，转内存兜底: %s", exc)

    now = time.time()
    records = get_cache(key) or []
    if not isinstance(records, list):
        records = []
    records = [t for t in records if now - float(t) < _AGENT_INQUIRY_RATE_WINDOW]
    if len(records) >= _AGENT_INQUIRY_RATE_LIMIT:
        raise HTTPException(429, "该来源提交过于频繁，请稍后再试")
    records.append(now)
    set_cache(key, records, timedelta(seconds=_AGENT_INQUIRY_RATE_WINDOW + 60))


def _tenant_products(db: Session, tenant_id: str) -> list[Product]:
    """按租户取上架未删产品（严格 tenant_id 过滤，不跨租户）。"""
    return (
        db.query(Product)
        .filter(
            Product.tenant_id == tenant_id,
            Product.deleted_at.is_(None),
            Product.is_active.is_(True),
        )
        .order_by(Product.sort_order.asc(), Product.created_at.desc())
        .all()
    )


def _offer_view(product: Product, base_url: str) -> dict[str, Any]:
    """把 Product 翻成 agent 可机读的 offer。

    关键纪律：库里没有的字段不许猜。价格 / MOQ / 认证状态一律
    `disclosed: false`，并把"该怎么问"写进 `ask_via`，逼着回到人工确认。
    """
    specs = product.specifications if isinstance(product.specifications, dict) else {}
    return {
        "id": product.id,
        "slug": product.slug,
        "name": product.name,
        "name_en": product.name_en or product.name,
        "subtitle": product.subtitle,
        "subtitle_en": product.subtitle_en,
        "description": product.description_en or product.description,
        "url": f"{base_url}/products/{product.slug}",
        "image_url": product.image_url,
        "attributes": {
            "fire_rating": {"value": product.fire_rating, "disclosed": bool(product.fire_rating)},
            "thermal_conductivity": {
                "value": product.thermal_conductivity,
                "disclosed": bool(product.thermal_conductivity),
            },
            "density": {"value": product.density, "disclosed": bool(product.density)},
            "strength": {"value": product.strength, "disclosed": bool(product.strength)},
            "unit_weight": {"value": product.unit_weight, "disclosed": bool(product.unit_weight)},
            "specifications": {"value": specs, "disclosed": bool(specs)},
        },
        "technical_params": product.technical_params_en or product.technical_params,
        "application_scenarios": product.application_scenarios_en or product.application_scenarios,
        "advantages": product.advantages_en or product.advantages,
        "price": {"value": None, "disclosed": False, "reason": "价格须人工报价，不在机读目录中承诺"},
        "moq": {"value": None, "disclosed": False, "reason": "起订量须人工确认"},
        "certifications": {"value": [], "disclosed": False, "reason": "认证状态须人工核验证书原件"},
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        "ask_via": "POST 本租户 /agent/inquiry（代客户发问）或由终端买家直接联系",
    }


@router.get("/tenants/{domain}/agent/manifest", summary="agent 出口自述（发现文档）")
def agent_manifest(domain: str, db: Session = Depends(get_db)) -> Any:
    """让采购 agent 一条请求就读到：能问什么、怎么问、边界在哪。"""
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    base = f"/api/v1/public/tenants/{domain}"
    product_count = db.query(Product).filter(
        Product.tenant_id == str(tenant.id),
        Product.deleted_at.is_(None),
        Product.is_active.is_(True),
    ).count()
    return success_response(
        data={
            "protocol": PROTOCOL_VERSION,
            "vendor": {
                "tenant_id": str(tenant.id),
                "name": tenant.name,
                "domain": domain,
                "platform": "优丁 YouDing",
            },
            "endpoints": {
                "catalog": {"method": "GET", "path": f"{base}/agent/catalog", "returns": "offers[]"},
                "match": {
                    "method": "POST",
                    "path": f"{base}/agent/match",
                    "body_schema": "ProductMatchRequest",
                    "returns": "matches[] + rejected[] + evidence",
                },
                "inquiry": {"method": "POST", "path": f"{base}/agent/inquiry", "returns": "inquiry_id"},
            },
            "human_readable": {
                "llms_txt": f"{base}/llms.txt",
                "llms_full_txt": f"{base}/llms-full.txt",
            },
            "catalog_size": product_count,
            # 明确声明能力边界，防止 agent 以为可以在这里完成交易
            "transactionable": False,
            "transaction_note": (
                "本出口支持选品与代客户提问，不支持下单、支付与合同成立。"
                "价格、MOQ、认证与交期一律须经人工确认后生效。"
            ),
            "rate_limits": {
                "inquiry": f"{_AGENT_INQUIRY_RATE_LIMIT} per {_AGENT_INQUIRY_RATE_WINDOW // 60} min per IP"
            },
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.get("/tenants/{domain}/agent/catalog", summary="租户产品机读目录（agent 选品用）")
def agent_catalog(
    domain: str,
    limit: int = Query(20, ge=1, le=_CATALOG_MAX),
    db: Session = Depends(get_db),
) -> Any:
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    base = f"/api/v1/public/tenants/{domain}"
    rows = _tenant_products(db, str(tenant.id))[:limit]
    data_readiness = None
    if not rows:
        # 目录空掉通常不是端点坏了，而是产品尚未完成租户归属回填（ADR-001：
        # products.tenant_id 目前仍允许 NULL）。把这层原因显式说出来，
        # 免得 agent 与运维都误判成"接口没数据/没接线"。
        data_readiness = (
            "该租户暂无已归属的上架产品：products.tenant_id 尚未完成回填"
            "（ADR-001 过渡期允许 NULL）。目录为空属数据就绪问题，非端点故障。"
        )
    return success_response(
        data={
            "protocol": PROTOCOL_VERSION,
            "tenant": tenant.name,
            "total": len(rows),
            "offers": [_offer_view(p, base) for p in rows],
            "data_readiness": data_readiness,
            "note": "未披露字段以 disclosed:false 明示，不得由 agent 自行推断填充。",
        }
    )


@router.post("/tenants/{domain}/agent/match", summary="按采购需求筛本租户产品（带证据）")
def agent_match(
    domain: str,
    payload: ProductMatchRequest,
    db: Session = Depends(get_db),
) -> Any:
    """复用平台既有 MatchingEngine（硬过滤 + 8 维加权 + 证据），但只在**本租户**产品内筛。

    与全站 /matching/product-match 的区别就一条：这里严格 tenant_id 过滤，
    所以租户可以放心把它开到自己的独立域上而不泄露别人的货。
    """
    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")
    rows = _tenant_products(db, str(tenant.id))
    if not rows:
        return success_response(
            data={
                "protocol": PROTOCOL_VERSION,
                "query": payload.model_dump(),
                "total_products": 0,
                "matches": [],
                "rejected": [],
                "note": "该租户暂无已发布产品，无法给出匹配结论。",
            }
        )
    product_views = [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "subtitle": p.subtitle,
            "image_url": p.image_url,
            "fire_rating": p.fire_rating,
            "thermal_conductivity": p.thermal_conductivity,
            "technical_params": p.technical_params or "",
            "application_scenarios": p.application_scenarios or "",
            "advantages": p.advantages or "",
            "specifications": p.specifications if isinstance(p.specifications, dict) else {},
            "category_id": p.category_id,
            "is_active": bool(p.is_active),
        }
        for p in rows
    ]
    result = MatchingEngine.match(product_views, payload.model_dump())
    result["protocol"] = PROTOCOL_VERSION
    result["tenant"] = tenant.name
    result["inquiry_endpoint"] = f"/api/v1/public/tenants/{domain}/agent/inquiry"
    return success_response(data=result)


@router.post("/tenants/{domain}/agent/inquiry", summary="采购 agent 代客户递交询盘")
def agent_inquiry(
    domain: str,
    body: AgentInquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """把 agent 收集到的采购需求递进**与官网表单同一条**询盘管线。

    与人工表单唯一的差别是多打三个来源标记：source_channel=ai_agent、
    attribution_channel=ai_search、ai_search_engine=agent 名，
    业务员在后台一眼能看出这是机器代发、代表谁、该按什么口径回话。
    """
    _check_agent_inquiry_rate(_client_ip(request))

    tenant = get_tenant_by_domain(db, domain)
    if not tenant:
        return error_response(404, "站点不存在")

    # 幂等：agent 超时重试不该产生第二条询盘（否则统计与跟进都会被灌水）
    if body.idempotency_key:
        dedupe_key = f"agent_inquiry:once:{tenant.id}:{body.idempotency_key}"
        if redis_client:
            try:
                if not redis_client.set(dedupe_key, "1", nx=True, ex=_AGENT_INQUIRY_RATE_WINDOW):
                    return success_response(
                        data={"accepted": True, "deduplicated": True},
                        message="该询盘此前已受理，未重复登记",
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("agent 询盘幂等检查失败，继续受理: %s", exc)

    product_line = body.product or (", ".join(body.product_slugs[:5]) if body.product_slugs else "")
    message = body.message
    if body.quantity:
        message += f"\n\n[需求量] {body.quantity}"
    if body.destination_country:
        message += f"\n[目的国] {body.destination_country}"
    if body.product_slugs:
        message += f"\n[意向产品] {', '.join(body.product_slugs)}"
    message += (
        f"\n\n[Agent 代发] {body.agent_name}（运营方：{body.agent_operator}）"
        + (f" 回话地址：{body.agent_url}" if body.agent_url else "")
    )

    from app.services.inquiries_unified_service import InquiriesUnifiedService

    try:
        created = InquiriesUnifiedService(db).create_public_lead(
            name=body.name,
            message=message,
            email=body.email,
            phone=body.phone,
            product=product_line or None,
            source_channel="ai_agent",
            tenant_id=str(tenant.id),
            landing_path=f"/api/v1/public/tenants/{domain}/agent/inquiry",
            last_click_label=f"agent:{body.agent_name[:60]}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent 询盘入库失败: %s", exc)
        raise HTTPException(500, "询盘未能登记，请稍后重试或改用页面表单") from exc

    inquiry_id = created.get("id") if isinstance(created, dict) else None
    return success_response(
        data={
            "protocol": PROTOCOL_VERSION,
            "inquiry_id": inquiry_id,
            "accepted": True,
            "deduplicated": False,
            "tenant": tenant.name,
            # 诚实回执：明确告诉 agent 这不是报价，别把这段话当成交条件回给买家
            "response_expected_from": "human_sales",
            "quoting": False,
            "note": "询盘已进入人工跟进队列。价格、MOQ、认证与交期需人工确认，本接口不予承诺。",
        },
        message="询盘已受理，将由业务员跟进",
    )
